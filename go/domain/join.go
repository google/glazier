// Copyright 2026 Google LLC
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

//go:build generate || windows
// +build generate windows

// Package join provides functions for domain joining a Windows client to a domain.
package join

import (
	"fmt"
	"unsafe"

	"golang.org/x/sys/windows"
)

// DomainJoinOptions specifies options for the domain join operation.
// See https://learn.microsoft.com/en-us/windows/win32/api/lmjoin/nf-lmjoin-netjoindomain
type DomainJoinOptions uint32

const (
	// JoinDomainFlag joins the domain specified in lpDomain.
	JoinDomainFlag DomainJoinOptions = 0x00000001
	// AcctCreate indicates that the caller will create the account on the domain.
	AcctCreate DomainJoinOptions = 0x00000002
	// AcctDelete indicates that lpAccount specifies an account to be deleted during an unjoin operation.
	AcctDelete DomainJoinOptions = 0x00000004
	// Win9XUpgrade indicates the join is part of a Win9x upgrade.
	Win9XUpgrade DomainJoinOptions = 0x00000010
	// DomainJoinIfJoined causes NetJoinDomain to function even if the workstation is already joined to lpDomain.
	DomainJoinIfJoined DomainJoinOptions = 0x00000020
	// JoinUnsecure performs an unsecure join.
	JoinUnsecure DomainJoinOptions = 0x00000040
	// MachinePwdPassed indicates that the machine password is being passed.
	MachinePwdPassed DomainJoinOptions = 0x00000080
	// DeferSpnSet defers setting the SPN.
	DeferSpnSet DomainJoinOptions = 0x00000100
	// JoinDCAccount performs a join as a DC account.
	JoinDCAccount DomainJoinOptions = 0x00000200
	// JoinWithNewName performs a join with a new name.
	JoinWithNewName DomainJoinOptions = 0x00000400
	// InstallInvocation indicates an install invocation.
	InstallInvocation DomainJoinOptions = 0x00001000
	// IgnoreUnsupportedFlags ignores unsupported flags.
	IgnoreUnsupportedFlags DomainJoinOptions = 0x10000000
)

var (
	modnetapi         = windows.NewLazySystemDLL("netapi32.dll")
	prodNetJoinDomain = modnetapi.NewProc("NetJoinDomain")
	netJoinDomain     = prodNetJoinDomain.Call
)

// Domain joins the local machine to a domain.
// See https://learn.microsoft.com/en-us/windows/win32/api/lmjoin/nf-lmjoin-netjoindomain for more details.
func Domain(domain, joinOU, joinAccount, joinPassword string, options DomainJoinOptions) error {

	dom, err := windows.UTF16PtrFromString(domain)
	if err != nil {
		return err
	}
	acc, err := windows.UTF16PtrFromString(joinAccount)
	if err != nil {
		return err
	}
	var ou *uint16
	if joinOU != "" {
		var err error
		ou, err = windows.UTF16PtrFromString(joinOU)
		if err != nil {
			return err
		}
	}
	pw, err := windows.UTF16PtrFromString(joinPassword)
	if err != nil {
		return err
	}
	fmt.Printf("Attempting domain join with domain: %s, OU: %s, account: %s\n", domain, joinOU, joinAccount)
	// https://learn.microsoft.com/en-us/windows/win32/api/lmjoin/nf-lmjoin-netjoindomain#parameters
	if returnCode, _, _ := netJoinDomain(
		0,                            // lpServer, 0 / Null means use the local machine.
		uintptr(unsafe.Pointer(dom)), // lpDomain
		uintptr(unsafe.Pointer(ou)),  // lpMachineAccountOU
		uintptr(unsafe.Pointer(acc)), // lpAccount
		uintptr(unsafe.Pointer(pw)),  // lpPassword
		uintptr(options),             // fJoinOptions
	); windows.Errno(returnCode) != windows.ERROR_SUCCESS {
		return fmt.Errorf("failed to join domain: %w", windows.Errno(returnCode))
	}

	fmt.Println("Domain join successful.")
	return nil
}
