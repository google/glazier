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

// +build windows

// Package device supports querying information about the local device.
package device

import (
	"errors"
	"fmt"
	"os"

	"github.com/StackExchange/wmi"
)

var (
	// ErrWMIEmptyResult indicates a condition where WMI failed to return the expected values.
	ErrWMIEmptyResult = errors.New("WMI returned without error, but zero results")
)

// Win32_SystemEnclosure models the WMI object of the same name.
type Win32_SystemEnclosure struct {
	ChassisTypes []int
}

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

// ChassisType attempts to distinguish the chassis type for the device.
func ChassisType() (Type, error) {
	var result []Win32_SystemEnclosure
	if err := wmi.Query(wmi.CreateQuery(&result, ""), &result); err != nil {
		return Unknown, err
	}
	if len(result) < 1 || len(result[0].ChassisTypes) < 1 {
		return Unknown, ErrWMIEmptyResult
	}
	switch result[0].ChassisTypes[0] {
	case -1:
		return Unknown, nil
	case 3, 35:
		return Desktop, nil
	case 8, 9, 10, 11, 12, 14, 30, 31, 32:
		return Laptop, nil
	default:
		return Other, nil
	}
}

// Win32_ComputerSystem models the WMI object of the same name.
type Win32_ComputerSystem struct {
	DNSHostName string
	Domain      string
	DomainRole  int
	Model       string
}

func sysInfo() (*Win32_ComputerSystem, error) {
	var result []Win32_ComputerSystem
	if err := wmi.Query(wmi.CreateQuery(&result, ""), &result); err != nil {
		return nil, err
	}
	if len(result) < 1 {
		return nil, ErrWMIEmptyResult
	}
	return &result[0], nil
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

// GetDomainRole attempts to determine the host's Active Directory role.
func GetDomainRole() (DomainRole, error) {
	si, err := sysInfo()
	if err != nil {
		return RoleUnknown, err
	}
	switch si.DomainRole {
	case 0, 1:
		return Workstation, nil
	case 2, 3:
		return Server, nil
	case 4, 5:
		return DomainController, nil
	default:
		return RoleUnknown, nil
	}
}

// Model returns the system model.
func Model() (string, error) {
	si, err := sysInfo()
	if err != nil {
		return "unknown", err
	}
	return si.Model, nil
}

// Win32_NTDomain models the WMI object of the same name.
type Win32_NTDomain struct {
	ClientSiteName       string
	DomainControllerName string
}

// Site returns the client's Active Directory site code.
func Site(domain string) (string, error) {
	var result []Win32_NTDomain
	err := wmi.Query(wmi.CreateQuery(&result, fmt.Sprintf("WHERE DomainName='%s'", domain)), &result)
	if err == nil && len(result) > 0 {
		return result[0].ClientSiteName, nil
	}
	return "", err
}

// UserProfiles returns a list of user profiles on the local device.
func UserProfiles() ([]string, error) {
	users := []string{}
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
