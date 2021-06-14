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

	"github.com/google/logger"
	"github.com/go-ole/go-ole"
	"github.com/go-ole/go-ole/oleutil"
	"github.com/iamacarpet/go-win64api"
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

type wmi struct {
	intf *ole.IDispatch
	svc  *ole.IDispatch
}

func (w *wmi) connect() error {
	unknown, err := oleutil.CreateObject("WbemScripting.SWbemLocator")
	if err != nil {
		return fmt.Errorf("unable to create initial object, %w", err)
	}
	defer unknown.Release()
	w.intf, err = unknown.QueryInterface(ole.IID_IDispatch)
	if err != nil {
		return fmt.Errorf("unable to create initial object, %w", err)
	}
	serviceRaw, err := oleutil.CallMethod(w.intf, "ConnectServer", nil, `\\.\ROOT\CIMV2\Security\MicrosoftVolumeEncryption`)
	if err != nil {
		return fmt.Errorf("permission denied: %w", err)
	}
	w.svc = serviceRaw.ToIDispatch()
	return nil
}

func (w *wmi) close() {
	w.svc.Release()
	w.intf.Release()
}

const (
	// Encryption Methods
	// https://docs.microsoft.com/en-us/windows/win32/secprov/getencryptionmethod-win32-encryptablevolume
	None int32 = iota
	AES128WithDiffuser
	AES256WithDiffuser
	AES128
	AES256
	HardwareEncryption
	XtsAES128
	XtsAES256

	// Encryption Flags
	// https://docs.microsoft.com/en-us/windows/win32/secprov/encrypt-win32-encryptablevolume
	EncryptDataOnly    int32 = 0x00000001
	EncryptDemandWipe  int32 = 0x00000002
	EncryptSynchronous int32 = 0x00010000

	// Error Codes
	ERROR_IO_DEVICE        int32 = -2147023779
	FVE_E_BOOTABLE_CDDVD   int32 = -2144272336
	FVE_E_PROTECTOR_EXISTS int32 = -2144272335
)

func encryptErrHandler(val int32) error {
	switch val {
	case ERROR_IO_DEVICE:
		return fmt.Errorf("an I/O error has occurred during encryption; the device may need to be reset")
	case FVE_E_BOOTABLE_CDDVD:
		return fmt.Errorf("BitLocker Drive Encryption detected bootable media (CD or DVD) in the computer. " +
			"Remove the media and restart the computer before configuring BitLocker.")
	case FVE_E_PROTECTOR_EXISTS:
		return fmt.Errorf("key protector cannot be added; only one key protector of this type is allowed for this drive")
	default:
		return fmt.Errorf("error code returned during encryption: %d", val)
	}
}

// EncryptWithTPM encrypts the drive with Bitlocker using TPM key protection.
//
// Example: bitlocker.EncryptWithTPM("c:", bitlocker.XtsAES256, bitlocker.EncryptDataOnly)
func EncryptWithTPM(driveLetter string, method int32, flags int32) error {
	ole.CoInitialize(0)
	defer ole.CoUninitialize()
	w := &wmi{}
	if err := w.connect(); err != nil {
		return fmt.Errorf("wmi.Connect: %w", err)
	}
	defer w.close()
	raw, err := oleutil.CallMethod(w.svc, "ExecQuery",
		"SELECT * FROM Win32_EncryptableVolume WHERE DriveLetter = '"+driveLetter+"'")
	if err != nil {
		return fmt.Errorf("ExecQuery: %w", err)
	}
	result := raw.ToIDispatch()
	defer result.Release()

	itemRaw, err := oleutil.CallMethod(result, "ItemIndex", 0)
	if err != nil {
		return fmt.Errorf("failed to fetch result row while processing BitLocker info: %w", err)
	}
	item := itemRaw.ToIDispatch()
	defer item.Release()

	// https://docs.microsoft.com/en-us/windows/win32/secprov/protectkeywithtpm-win32-encryptablevolume
	var volumeKeyProtectorID ole.VARIANT
	ole.VariantInit(&volumeKeyProtectorID)
	resultRaw, err := oleutil.CallMethod(item, "ProtectKeyWithTPM", nil, nil, &volumeKeyProtectorID)
	if err != nil {
		return fmt.Errorf("ProtectKeyWithTPM(%s): %w", driveLetter, err)
	} else if val, ok := resultRaw.Value().(int32); val != 0 || !ok {
		return fmt.Errorf("ProtectKeyWithTPM(%s): %w", driveLetter, encryptErrHandler(val))
	}

	resultRaw, err = oleutil.CallMethod(item, "Encrypt", method, flags)
	if err != nil {
		return fmt.Errorf("Encrypt(%s): %w", driveLetter, err)
	} else if val, ok := resultRaw.Value().(int32); val != 0 || !ok {
		return fmt.Errorf("Encrypt(%s): %w", driveLetter, encryptErrHandler(val))
	}
	return nil
}
