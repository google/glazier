// Copyright 2021 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

// Package bitlocker provides functionality for managing Bitlocker.
package bitlocker

import (
	"fmt"

	"github.com/scjalliance/comshim"
	"github.com/google/logger"
	"github.com/go-ole/go-ole"
	"github.com/go-ole/go-ole/oleutil"
	"github.com/iamacarpet/go-win64api/winapi"
)

var (
	// Test Helpers
	funcBackup       = winapi.BackupBitLockerRecoveryKeys
	funcRecoveryInfo = winapi.GetBitLockerRecoveryInfo
)

// BackupToAD backs up Bitlocker recovery keys to Active Directory.
func BackupToAD() error {
	infos, err := funcRecoveryInfo()
	if err != nil {
		return err
	}
	volIDs := []string{}
	for _, i := range infos {
		if i.ConversionStatus != 1 {
			logger.Warningf("Skipping volume %s due to conversion status (%d).", i.DriveLetter, i.ConversionStatus)
			continue
		}
		logger.Infof("Backing up Bitlocker recovery password for drive %q.", i.DriveLetter)
		volIDs = append(volIDs, i.PersistentVolumeID)
	}
	return funcBackup(volIDs)
}

// Encryption Methods
// https://docs.microsoft.com/en-us/windows/win32/secprov/getencryptionmethod-win32-encryptablevolume
type EncryptionMethod int32

const (
	None EncryptionMethod = iota
	AES128WithDiffuser
	AES256WithDiffuser
	AES128
	AES256
	HardwareEncryption
	XtsAES128
	XtsAES256
)

// Encryption Flags
// https://docs.microsoft.com/en-us/windows/win32/secprov/encrypt-win32-encryptablevolume
type EncryptionFlag int32

const (
	EncryptDataOnly    EncryptionFlag = 0x00000001
	EncryptDemandWipe  EncryptionFlag = 0x00000002
	EncryptSynchronous EncryptionFlag = 0x00010000

	// Error Codes
	ERROR_IO_DEVICE                     int32 = -2147023779
	FVE_E_EDRIVE_INCOMPATIBLE_VOLUME    int32 = -2144272206
	FVE_E_NO_TPM_WITH_PASSPHRASE        int32 = -2144272212
	FVE_E_PASSPHRASE_TOO_LONG           int32 = -2144272214
	FVE_E_POLICY_PASSPHRASE_NOT_ALLOWED int32 = -2144272278
	FVE_E_NOT_DECRYPTED                 int32 = -2144272327
	FVE_E_INVALID_PASSWORD_FORMAT       int32 = -2144272331
	FVE_E_BOOTABLE_CDDVD                int32 = -2144272336
	FVE_E_PROTECTOR_EXISTS              int32 = -2144272335
)

func encryptErrHandler(val int32) error {
	switch val {
	case ERROR_IO_DEVICE:
		return fmt.Errorf("an I/O error has occurred during encryption; the device may need to be reset")
	case FVE_E_EDRIVE_INCOMPATIBLE_VOLUME:
		return fmt.Errorf("the drive specified does not support hardware-based encryption")
	case FVE_E_NO_TPM_WITH_PASSPHRASE:
		return fmt.Errorf("a TPM key protector cannot be added because a password protector exists on the drive")
	case FVE_E_PASSPHRASE_TOO_LONG:
		return fmt.Errorf("the passphrase cannot exceed 256 characters")
	case FVE_E_POLICY_PASSPHRASE_NOT_ALLOWED:
		return fmt.Errorf("Group Policy settings do not permit the creation of a password")
	case FVE_E_NOT_DECRYPTED:
		return fmt.Errorf("the drive must be fully decrypted to complete this operation")
	case FVE_E_INVALID_PASSWORD_FORMAT:
		return fmt.Errorf("the format of the recovery password provided is invalid")
	case FVE_E_BOOTABLE_CDDVD:
		return fmt.Errorf("BitLocker Drive Encryption detected bootable media (CD or DVD) in the computer. " +
			"Remove the media and restart the computer before configuring BitLocker.")
	case FVE_E_PROTECTOR_EXISTS:
		return fmt.Errorf("key protector cannot be added; only one key protector of this type is allowed for this drive")
	default:
		return fmt.Errorf("error code returned during encryption: %d", val)
	}
}

// A Volume tracks an open encryptable volume.
type Volume struct {
	letter  string
	handle  *ole.IDispatch
	wmiIntf *ole.IDispatch
	wmiSvc  *ole.IDispatch
}

// Close frees all resources associated with a volume.
func (v *Volume) Close() {
	v.handle.Release()
	v.wmiIntf.Release()
	v.wmiSvc.Release()
	comshim.Done()
}

// Connect connects to an encryptable volume in order to manage it.
// You must call Close() to release the volume when finished.
//
// Example: bitlocker.Connect("c:")
func Connect(driveLetter string) (Volume, error) {
	comshim.Add(1)
	v := Volume{letter: driveLetter}

	unknown, err := oleutil.CreateObject("WbemScripting.SWbemLocator")
	if err != nil {
		comshim.Done()
		return v, fmt.Errorf("CreateObject: %w", err)
	}
	defer unknown.Release()
	v.wmiIntf, err = unknown.QueryInterface(ole.IID_IDispatch)
	if err != nil {
		comshim.Done()
		return v, fmt.Errorf("QueryInterface: %w", err)
	}
	serviceRaw, err := oleutil.CallMethod(v.wmiIntf, "ConnectServer", nil, `\\.\ROOT\CIMV2\Security\MicrosoftVolumeEncryption`)
	if err != nil {
		v.Close()
		return v, fmt.Errorf("ConnectServer: %w", err)
	}
	v.wmiSvc = serviceRaw.ToIDispatch()

	raw, err := oleutil.CallMethod(v.wmiSvc, "ExecQuery", "SELECT * FROM Win32_EncryptableVolume WHERE DriveLetter = '"+driveLetter+"'")
	if err != nil {
		v.Close()
		return v, fmt.Errorf("ExecQuery: %w", err)
	}
	result := raw.ToIDispatch()
	defer result.Release()

	itemRaw, err := oleutil.CallMethod(result, "ItemIndex", 0)
	if err != nil {
		v.Close()
		return v, fmt.Errorf("failed to fetch result row while processing BitLocker info: %w", err)
	}
	v.handle = itemRaw.ToIDispatch()

	return v, nil
}

// Encrypt encrypts the volume.
//
// Example: vol.Encrypt(bitlocker.XtsAES256, bitlocker.EncryptDataOnly)
//
// Ref: https://docs.microsoft.com/en-us/windows/win32/secprov/protectkeywithtpm-win32-encryptablevolume
func (v *Volume) Encrypt(method EncryptionMethod, flags EncryptionFlag) error {
	resultRaw, err := oleutil.CallMethod(v.handle, "Encrypt", int32(method), int32(flags))
	if err != nil {
		return fmt.Errorf("Encrypt(%s): %w", v.letter, err)
	} else if val, ok := resultRaw.Value().(int32); val != 0 || !ok {
		return fmt.Errorf("Encrypt(%s): %w", v.letter, encryptErrHandler(val))
	}

	return nil
}

// DiscoveryVolumeType specifies the type of discovery volume to be used by Prepare.
//
// Ref: https://docs.microsoft.com/en-us/windows/win32/secprov/preparevolume-win32-encryptablevolume
type DiscoveryVolumeType string

const (
	// VolumeTypeNone indicates no discovery volume. This value creates a native BitLocker volume.
	VolumeTypeNone DiscoveryVolumeType = "<none>"
	// VolumeTypeDefault indicates the default behavior.
	VolumeTypeDefault DiscoveryVolumeType = "<default>"
	// VolumeTypeFAT32 creates a FAT32 discovery volume.
	VolumeTypeFAT32 DiscoveryVolumeType = "FAT32"
)

// ForceEncryptionType specifies the encryption type to be used when calling Prepare on the volume.
//
// Ref: https://docs.microsoft.com/en-us/windows/win32/secprov/preparevolume-win32-encryptablevolume
type ForceEncryptionType int32

const (
	// EncryptionTypeUnspecified indicates that the encryption type is not specified.
	EncryptionTypeUnspecified ForceEncryptionType = 0
	// EncryptionTypeSoftware specifies software encryption.
	EncryptionTypeSoftware ForceEncryptionType = 1
	// EncryptionTypeHardware specifies hardware encryption.
	EncryptionTypeHardware ForceEncryptionType = 2
)

// Prepare prepares a new Bitlocker Volume. This should be called BEFORE any key protectors are added.
//
// Example: vol.Prepare(bitlocker.VolumeTypeDefault, bitlocker.EncryptionTypeHardware)
//
// Ref: https://docs.microsoft.com/en-us/windows/win32/secprov/preparevolume-win32-encryptablevolume
func (v *Volume) Prepare(volType DiscoveryVolumeType, encType ForceEncryptionType) error {
	resultRaw, err := oleutil.CallMethod(v.handle, "PrepareVolume", string(volType), int32(encType))
	if err != nil {
		return fmt.Errorf("PrepareVolume(%s): %w", v.letter, err)
	} else if val, ok := resultRaw.Value().(int32); val != 0 || !ok {
		return fmt.Errorf("PrepareVolume(%s): %w", v.letter, encryptErrHandler(val))
	}
	return nil
}

// ProtectWithNumericalPassword adds a numerical password key protector.
//
// Leave password as a blank string to have one auto-generated by Windows. (Recommended)
//
// In Powershell this is referred to as a RecoveryPasswordProtector.
//
// Ref: https://docs.microsoft.com/en-us/windows/win32/secprov/protectkeywithnumericalpassword-win32-encryptablevolume
func (v *Volume) ProtectWithNumericalPassword(password string) error {
	var volumeKeyProtectorID ole.VARIANT
	ole.VariantInit(&volumeKeyProtectorID)
	var resultRaw *ole.VARIANT
	var err error
	if password != "" {
		resultRaw, err = oleutil.CallMethod(v.handle, "ProtectWithNumericalPassword", nil, password, &volumeKeyProtectorID)
	} else {
		resultRaw, err = oleutil.CallMethod(v.handle, "ProtectWithNumericalPassword", nil, nil, &volumeKeyProtectorID)
	}
	if err != nil {
		return fmt.Errorf("ProtectWithNumericalPassword(%s): %w", v.letter, err)
	} else if val, ok := resultRaw.Value().(int32); val != 0 || !ok {
		return fmt.Errorf("ProtectWithNumericalPassword(%s): %w", v.letter, encryptErrHandler(val))
	}

	return nil
}

// ProtectWithPassphrase adds a passphrase key protector.
//
// Ref: https://docs.microsoft.com/en-us/windows/win32/secprov/protectkeywithpassphrase-win32-encryptablevolume
func (v *Volume) ProtectWithPassphrase(passphrase string) error {
	var volumeKeyProtectorID ole.VARIANT
	ole.VariantInit(&volumeKeyProtectorID)
	resultRaw, err := oleutil.CallMethod(v.handle, "ProtectKeyWithPassphrase", nil, passphrase, &volumeKeyProtectorID)
	if err != nil {
		return fmt.Errorf("ProtectWithPassphrase(%s): %w", v.letter, err)
	} else if val, ok := resultRaw.Value().(int32); val != 0 || !ok {
		return fmt.Errorf("ProtectWithPassphrase(%s): %w", v.letter, encryptErrHandler(val))
	}

	return nil
}

// ProtectWithTPM adds the TPM key protector.
//
// Ref: https://docs.microsoft.com/en-us/windows/win32/secprov/protectkeywithtpm-win32-encryptablevolume
func (v *Volume) ProtectWithTPM() error {
	var volumeKeyProtectorID ole.VARIANT
	ole.VariantInit(&volumeKeyProtectorID)
	resultRaw, err := oleutil.CallMethod(v.handle, "ProtectKeyWithTPM", nil, nil, &volumeKeyProtectorID)
	if err != nil {
		return fmt.Errorf("ProtectKeyWithTPM(%s): %w", v.letter, err)
	} else if val, ok := resultRaw.Value().(int32); val != 0 || !ok {
		return fmt.Errorf("ProtectKeyWithTPM(%s): %w", v.letter, encryptErrHandler(val))
	}

	return nil
}
