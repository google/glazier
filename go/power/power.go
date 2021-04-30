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

// Package power provides utilities for managing system power state.
package power

import (
	"golang.org/x/sys/windows"
)

// Flag mirrors Windows exit flags
// https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-exitwindowsex
type Flag uint32

const (
	EWX_LOGOFF   = Flag(0x00000000)
	EWX_POWEROFF = Flag(0x00000008)
	EWX_REBOOT   = Flag(0x00000002)
	EWX_SHUTDOWN = Flag(0x00000001)
)

// Reason Codes for system shutdown
// https://docs.microsoft.com/en-us/windows/win32/shutdown/system-shutdown-reason-codes
type Reason uint32

const (
	SHTDN_REASON_MINOR_OTHER        = Reason(0x00000000)
	SHTDN_REASON_MINOR_MAINTENANCE  = Reason(0x00000001)
	SHTDN_REASON_MINOR_INSTALLATION = Reason(0x00000002)
	SHTDN_REASON_MINOR_UPGRADE      = Reason(0x00000003)
	SHTDN_REASON_MINOR_RECONFIG     = Reason(0x00000004)
)

// Exit exits the active session using custom settings.
//
// Example: Exit(EWX_LOGOFF, SHTDN_REASON_MINOR_MAINTENANCE)
func Exit(flag Flag, reason Reason) error {
	return windows.ExitWindowsEx(uint32(flag), uint32(reason))
}

// Reboot reboots the system.
//
// Example: Reboot(SHTDN_REASON_MINOR_MAINTENANCE)
func Reboot(reason Reason) error {
	return windows.ExitWindowsEx(uint32(EWX_REBOOT), uint32(reason))
}

// Shutdown shuts down the system.
//
// Example: Shutdown(SHTDN_REASON_MINOR_MAINTENANCE)
func Shutdown(reason Reason) error {
	return windows.ExitWindowsEx(uint32(EWX_SHUTDOWN), uint32(reason))
}
