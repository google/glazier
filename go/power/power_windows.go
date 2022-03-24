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

//go:build windows
// +build windows

// Package power provides utilities for managing system power state.
package power

import (
	"fmt"
	"syscall"

	"golang.org/x/sys/windows"
)

// Flag mirrors Windows exit flags
// https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-exitwindowsex
type Flag uint32

const (
	EWX_LOGOFF   = Flag(windows.EWX_LOGOFF)
	EWX_SHUTDOWN = Flag(windows.EWX_SHUTDOWN)
	EWX_REBOOT   = Flag(windows.EWX_REBOOT)
	EWX_FORCE    = Flag(windows.EWX_FORCE)
	EWX_POWEROFF = Flag(windows.EWX_POWEROFF)
)

// Reason Codes for system shutdown
// https://docs.microsoft.com/en-us/windows/win32/shutdown/system-shutdown-reason-codes
type Reason uint32

const (
	SHTDN_REASON_MINOR_OTHER           = Reason(windows.SHTDN_REASON_MINOR_OTHER)
	SHTDN_REASON_MINOR_MAINTENANCE     = Reason(windows.SHTDN_REASON_MINOR_MAINTENANCE)
	SHTDN_REASON_MINOR_INSTALLATION    = Reason(windows.SHTDN_REASON_MINOR_INSTALLATION)
	SHTDN_REASON_MINOR_UPGRADE         = Reason(windows.SHTDN_REASON_MINOR_UPGRADE)
	SHTDN_REASON_MINOR_RECONFIG        = Reason(windows.SHTDN_REASON_MINOR_RECONFIG)
	SHTDN_REASON_MAJOR_NONE            = Reason(windows.SHTDN_REASON_MAJOR_NONE)
	SHTDN_REASON_MAJOR_HARDWARE        = Reason(windows.SHTDN_REASON_MAJOR_HARDWARE)
	SHTDN_REASON_MAJOR_OPERATINGSYSTEM = Reason(windows.SHTDN_REASON_MAJOR_OPERATINGSYSTEM)
	SHTDN_REASON_MAJOR_SOFTWARE        = Reason(windows.SHTDN_REASON_MAJOR_SOFTWARE)
	SHTDN_REASON_MAJOR_APPLICATION     = Reason(windows.SHTDN_REASON_MAJOR_APPLICATION)
	SHTDN_REASON_MAJOR_SYSTEM          = Reason(windows.SHTDN_REASON_MAJOR_SYSTEM)
)

// Privileges
const (
	SE_SHUTDOWN_NAME = "SeShutdownPrivilege"
)

// To shut down or restart the system, the calling process must use the AdjustTokenPrivileges function to enable the SE_SHUTDOWN_NAME privilege.
// Ref: https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-exitwindowsex
func setPrivToken() error {
	var hToken windows.Token
	err := windows.OpenProcessToken(windows.CurrentProcess(), windows.TOKEN_ADJUST_PRIVILEGES|windows.TOKEN_QUERY, &hToken)
	if err != nil {
		return fmt.Errorf("windows.OpenProcessToken: %w", err)
	}
	defer hToken.Close()

	tkp := windows.Tokenprivileges{}
	err = windows.LookupPrivilegeValue(nil, syscall.StringToUTF16Ptr(SE_SHUTDOWN_NAME), &tkp.Privileges[0].Luid)
	if err != nil {
		return fmt.Errorf("windows.LookupPrivilegeValue: %w", err)
	}

	tkp.PrivilegeCount = 1
	tkp.Privileges[0].Attributes = windows.SE_PRIVILEGE_ENABLED

	err = windows.AdjustTokenPrivileges(hToken, false, &tkp, 0, nil, nil)
	if err != nil {
		return fmt.Errorf("windows.AdjustTokenPrivileges: %w", err)
	}
	return nil
}

// Exit exits the active session using custom settings.
//
// Example: Exit(EWX_LOGOFF, SHTDN_REASON_MINOR_MAINTENANCE)
func Exit(flag Flag, reason Reason) error {
	return windows.ExitWindowsEx(uint32(flag), uint32(reason))
}

// Reboot reboots the system.
//
// Example: Reboot(SHTDN_REASON_MINOR_MAINTENANCE, true)
func Reboot(reason Reason, force bool) error {
	if err := setPrivToken(); err != nil {
		return err
	}
	fl := uint32(EWX_REBOOT)
	if force {
		fl = fl | uint32(EWX_FORCE)
	}
	return windows.ExitWindowsEx(fl, uint32(reason))
}

// Shutdown shuts down the system.
//
// Example: Shutdown(SHTDN_REASON_MINOR_MAINTENANCE, true)
func Shutdown(reason Reason, force bool) error {

	if err := setPrivToken(); err != nil {
		return err
	}
	fl := uint32(EWX_SHUTDOWN)
	if force {
		fl = fl | uint32(EWX_FORCE)
	}

	return windows.ExitWindowsEx(fl, uint32(reason))
}
