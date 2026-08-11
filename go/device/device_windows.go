//go:build windows

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

// Package device supports querying information about the local device.
package device

import (
	"bytes"
	"encoding/binary"
	"errors"
	"fmt"
	"os"
	"strings"
	"unsafe"

	reg "golang.org/x/sys/windows/registry"
	"golang.org/x/sys/windows"
	"github.com/StackExchange/wmi"
)

var (
	// ErrWMIEmptyResult indicates a condition where WMI failed to return the expected values.
	ErrWMIEmptyResult = errors.New("WMI returned without error, but zero results")

	kernelDLL                  = windows.NewLazySystemDLL("kernel32.dll")
	procGetSystemFirmwareTable = kernelDLL.NewProc("GetSystemFirmwareTable")

	tbsDLL           = windows.NewLazySystemDLL("tbs.dll")
	tbsCreateContext = tbsDLL.NewProc("Tbsi_Context_Create")
	tbsContextClose  = tbsDLL.NewProc("Tbsip_Context_Close")
	tbsSubmitCommand = tbsDLL.NewProc("Tbsip_Submit_Command")

	// Test helpers.
	getChassisType        = chassisTypeSMBIOS
	getTPMSpecVersion     = getTPMSpecVersionFromTBS
	netGetJoinInformation = windows.NetGetJoinInformation
	netAPIBufferFree      = windows.NetApiBufferFree
	registryGetString     = regGetString
	wmiQuery              = wmi.Query
)

const (
	// https://github.com/digitalocean/go-smbios/blob/390a4f403a8e94ca0acdcf609eb18eeae9d6d1ac/smbios/stream_windows.go#L34
	providerRSMB = 0x52534D42
)

// Type is a device type as reported by the system enclosure.
type Type string

var (
	// Laptop indicates a laptop chassis.
	Laptop Type = "Laptop"
	// Desktop indicates a desktop chassis.
	Desktop Type = "Desktop"
	// Other indicates an "other" chassis type.
	Other Type = "Other"
	// Unknown indicates an "unknown" chassis type.
	Unknown Type = "Unknown"
)

func chassisTypeSMBIOS() (Type, error) {
	bufSize, _, err := procGetSystemFirmwareTable.Call(uintptr(providerRSMB), 0, 0, 0)
	if bufSize == 0 {
		return Unknown, fmt.Errorf("GetSystemFirmwareTable failed: %w", err)
	}
	buf := make([]byte, bufSize)
	returnCode, _, err := procGetSystemFirmwareTable.Call(uintptr(providerRSMB), 0, uintptr(unsafe.Pointer(&buf[0])), uintptr(bufSize))
	if returnCode == 0 {
		return Unknown, fmt.Errorf("GetSystemFirmwareTable failed: %w", err)
	}
	if len(buf) < 8 {
		return Unknown, errors.New("SMBIOS buffer too short")
	}
	tableData := buf[8:]
	offset := 0
	for offset+4 <= len(tableData) {
		structType := tableData[offset]
		structLen := int(tableData[offset+1])
		if structLen < 4 || offset+structLen > len(tableData) {
			break
		}
		if structType == 3 { // Type 3: System Enclosure or Chassis.
			if structLen > 5 {
				rawType := int(tableData[offset+5] & 0x7F)
				switch rawType {
				case 0:
					return Unknown, nil
				case 3, 35:
					return Desktop, nil
				case 8, 9, 10, 11, 12, 14, 30, 31, 32:
					return Laptop, nil
				default:
					return Other, nil
				}
			}
		}
		// 127 is the end-of-table indicator.
		if structType == 127 {
			break
		}
		offset += structLen
		for offset+1 < len(tableData) && (tableData[offset] != 0 || tableData[offset+1] != 0) {
			offset++
		}
		offset += 2
	}
	return Unknown, nil
}

// ChassisType attempts to distinguish the chassis type for the device.
func ChassisType() (Type, error) {
	t, err := getChassisType()
	if err != nil {
		return t, fmt.Errorf("failed to get chassis type from SMBIOS: %w", err)
	}
	return t, nil
}

// DomainRole indicates the role of a host on an Active Directory domain.
type DomainRole string

var (
	// Workstation corresponds to a domain workstation.
	Workstation DomainRole = "Workstation"
	// Server corresponds to a domain server.
	Server DomainRole = "Server"
	// DomainController corresponds to an Active Directory domain controller.
	DomainController DomainRole = "Domain Controller"
	// RoleUnknown indicates an unknown domain role.
	RoleUnknown DomainRole = "Unknown"
)

func regGetString(path, name string) (string, error) {
	k, err := reg.OpenKey(reg.LOCAL_MACHINE, path, reg.READ)
	if err != nil {
		return "", err
	}
	defer k.Close()
	val, _, err := k.GetStringValue(name)
	return val, err
}

// GetDomainRole attempts to determine the host's Active Directory role.
func GetDomainRole() (DomainRole, error) {
	productType, err := registryGetString(`SYSTEM\CurrentControlSet\Control\ProductOptions`, "ProductType")
	if err != nil {
		return RoleUnknown, err
	}
	switch productType {
	case "WinNT":
		return Workstation, nil
	case "ServerNT":
		return Server, nil
	case "LanmanNT":
		return DomainController, nil
	default:
		return RoleUnknown, nil
	}
}

// GetDomainJoined returns if a machine is joined to a domain.
func GetDomainJoined() (bool, error) {
	var domainName *uint16
	var joinStatus uint32
	if err := netGetJoinInformation(nil, &domainName, &joinStatus); err != nil {
		return false, fmt.Errorf("NetGetJoinInformation failed: %w", err)
	}
	if domainName != nil {
		netAPIBufferFree((*byte)(unsafe.Pointer(domainName)))
	}
	return joinStatus == windows.NetSetupDomainName, nil
}

// Model returns the system model.
func Model() (string, error) {
	manufacturer, err := registryGetString(`HARDWARE\DESCRIPTION\System\BIOS`, "SystemManufacturer")
	if err != nil {
		return "unknown", fmt.Errorf("failed to get SystemManufacturer from registry: %w", err)
	}
	if strings.EqualFold(manufacturer, "lenovo") {
		family, err := registryGetString(`HARDWARE\DESCRIPTION\System\BIOS`, "SystemFamily")
		if err != nil {
			return "unknown", fmt.Errorf("failed to get SystemFamily from registry: %w", err)
		}
		return family, nil
	}
	model, err := registryGetString(`HARDWARE\DESCRIPTION\System\BIOS`, "SystemProductName")
	if err != nil {
		return "unknown", fmt.Errorf("failed to get SystemProductName from registry: %w", err)
	}
	return model, nil
}

// Win32_NTDomain models the WMI object of the same name.
type Win32_NTDomain struct {
	ClientSiteName       string
	DomainControllerName string
}

// Site returns the client's Active Directory site code.
func Site(domain string) (string, error) {
	var result []Win32_NTDomain
	err := wmiQuery(wmi.CreateQuery(&result, fmt.Sprintf("WHERE DomainName='%s'", domain)), &result)
	if err == nil && len(result) > 0 {
		return result[0].ClientSiteName, nil
	}
	return "", err
}

// UserProfiles returns a list of user profiles on the local device.
func UserProfiles() ([]string, error) {
	var users []string
	files, err := os.ReadDir(os.Getenv("SystemDrive") + `\Users`)
	if err != nil {
		return users, err
	}

	for _, f := range files {
		if f.IsDir() {
			users = append(users, f.Name())
		}
	}
	return users, nil
}

type tbsContextParams2 struct {
	version uint32
	flags   uint32
}

func getTPMSpecVersionFromTBS() (string, error) {
	var tbsContext uintptr
	params := tbsContextParams2{
		version: 2, // TPMVersion20
		flags:   6, // IncludeTPM12 (2) | IncludeTPM20 (4)
	}

	returnCode, _, _ := tbsCreateContext.Call(uintptr(unsafe.Pointer(&params)), uintptr(unsafe.Pointer(&tbsContext)))
	if returnCode != 0 {
		return "", fmt.Errorf("Tbsi_Context_Create failed: %w", windows.Errno(returnCode))
	}
	defer tbsContextClose.Call(tbsContext)

	// Send TPM2_GetCapability for TPM_PT_FAMILY_INDICATOR (0x100).
	cmd := []byte{
		0x80, 0x01, // TPM_ST_NO_SESSIONS
		0x00, 0x00, 0x00, 0x16, // Command Size = 22 bytes
		0x00, 0x00, 0x01, 0x7A, // TPM_CC_GetCapability
		0x00, 0x00, 0x00, 0x06, // TPM_CAP_TPM_PROPERTIES
		0x00, 0x00, 0x01, 0x00, // Property = TPM_PT_FAMILY_INDICATOR (0x100)
		0x00, 0x00, 0x00, 0x04, // PropertyCount = 4
	}

	resp := make([]byte, 1024)
	respLen := uint32(len(resp))

	const normalPriority = 200
	const commandLocalityZero = 0
	returnCode, _, _ = tbsSubmitCommand.Call(
		tbsContext,
		commandLocalityZero,
		normalPriority,
		uintptr(unsafe.Pointer(&cmd[0])),
		uintptr(len(cmd)),
		uintptr(unsafe.Pointer(&resp[0])),
		uintptr(unsafe.Pointer(&respLen)),
	)
	if returnCode == 0 && respLen >= 10 {
		rc := binary.BigEndian.Uint32(resp[6:10])
		if rc == 0 && respLen >= 19 {
			count := binary.BigEndian.Uint32(resp[15:19])
			var family string = "2.0"
			var level uint32 = 0
			var rev uint32 = 0
			var foundRev bool

			offset := 19
			for i := uint32(0); i < count && offset+8 <= int(respLen); i++ {
				prop := binary.BigEndian.Uint32(resp[offset : offset+4])
				val := binary.BigEndian.Uint32(resp[offset+4 : offset+8])
				switch prop {
				case 0x100: // TPM_PT_FAMILY_INDICATOR (ASCII "2.0\0").
					b := resp[offset+4 : offset+8]
					n := bytes.IndexByte(b, 0)
					if n == -1 {
						n = len(b)
					}
					family = string(b[:n])
				case 0x101: // TPM_PT_LEVEL
					level = val
				case 0x102: // TPM_PT_REVISION
					rev = val
					foundRev = true
				}
				offset += 8
			}

			if foundRev {
				return fmt.Sprintf("%s, %d, %d.%02d", family, level, rev/100, rev%100), nil
			}
		}
	}

	// Try TPM 1.2 GetCapability command if TPM 2.0 failed or on TPM 1.2.
	cmd12 := []byte{
		0x00, 0xC1, // TPM_TAG_RQU_COMMAND
		0x00, 0x00, 0x00, 0x12, // Command Size = 18 bytes
		0x00, 0x00, 0x00, 0x65, // TPM_ORD_GetCapability
		0x00, 0x00, 0x00, 0x1A, // TPM_CAP_VERSION_VAL
		0x00, 0x00, 0x00, 0x00, // SubCapSize = 0
	}
	respLen = uint32(len(resp))
	returnCode, _, _ = tbsSubmitCommand.Call(
		tbsContext,
		commandLocalityZero,
		normalPriority,
		uintptr(unsafe.Pointer(&cmd12[0])),
		uintptr(len(cmd12)),
		uintptr(unsafe.Pointer(&resp[0])),
		uintptr(unsafe.Pointer(&respLen)),
	)
	if returnCode == 0 && respLen >= 20 {
		rc := binary.BigEndian.Uint32(resp[6:10])
		if rc == 0 {
			major := resp[16]
			minor := resp[17]
			revMajor := resp[18]
			revMinor := resp[19]
			return fmt.Sprintf("%d.%d, %d, %d.%d", major, minor, revMajor, revMinor, 0), nil
		}
	}

	return "", errors.New("unable to retrieve TPM spec version from TBS")
}

// TPMVersion returns the version of the TPM on the host.
func TPMVersion() (string, error) {
	ver, err := getTPMSpecVersion()
	if err != nil {
		return "", err
	}
	return ver, nil
}
