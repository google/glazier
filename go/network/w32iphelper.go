// Copyright 2025 Google LLC
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

// Package w32iphelper provides functions for interacting with the IP Helper win32 APIs.
package w32iphelper

import (
	"fmt"
	"net"
	"os"
	"syscall"
	"unsafe"

	"golang.org/x/sys/windows"
)

var (
	modiphlpapi = windows.NewLazySystemDLL("iphlpapi.dll")

	// https://learn.microsoft.com/en-us/windows/win32/api/netioapi/nf-netioapi-createunicastipaddressentry
	procCreateUnicastIPAddressEntry = modiphlpapi.NewProc("CreateUnicastIpAddressEntry") // Set IP address
	// https://learn.microsoft.com/en-us/windows/win32/api/netioapi/nf-netioapi-setinterfacednssettings
	procSetInterfaceDNSSettings = modiphlpapi.NewProc("SetInterfaceDnsSettings") // set DNS settings
	// https://learn.microsoft.com/en-us/windows/win32/api/netioapi/nf-netioapi-setipforwardentry2
	procSetIPForwardEntry = modiphlpapi.NewProc("SetIpForwardEntry2") // Set IP forward entry
)

// NetworkAdapterProperties returns the network adapter with the given name.
func NetworkAdapterProperties(naflags GAAFlags, name string) (*windows.IpAdapterAddresses, error) {
	var b []byte
	// Recommended initial size: https://learn.microsoft.com/en-us/windows/win32/api/iphlpapi/nf-iphlpapi-getadaptersaddresses#remarks
	l := uint32(15000)
	for {
		b = make([]byte, l)
		// https://learn.microsoft.com/en-us/windows/win32/api/iphlpapi/nf-iphlpapi-getadaptersaddresses
		err := windows.GetAdaptersAddresses(syscall.AF_UNSPEC, uint32(naflags), 0, (*windows.IpAdapterAddresses)(unsafe.Pointer(&b[0])), &l)
		if err == nil {
			if l == 0 {
				return nil, nil
			}
			break
		}
		if err.(syscall.Errno) != syscall.ERROR_BUFFER_OVERFLOW {
			return nil, os.NewSyscallError("getadaptersaddresses", err)
		}
		if l <= uint32(len(b)) {
			return nil, os.NewSyscallError("getadaptersaddresses", err)
		}
	}
	for aa := (*windows.IpAdapterAddresses)(unsafe.Pointer(&b[0])); aa != nil; aa = aa.Next {
		if windows.BytePtrToString(aa.AdapterName) == name {
			return aa, nil
		}
	}
	return nil, fmt.Errorf("no adapter with name %q found", name)
}

// SetInterfaceDNSSettings sets the DNS settings for the given interface.
// https://learn.microsoft.com/en-us/windows/win32/api/netioapi/nf-netioapi-setinterfacednssettings
func SetInterfaceDNSSettings(guid *windows.GUID, settings *DNSInterfaceSettings) error {
	if returnCode, _, err := procSetInterfaceDNSSettings.Call(uintptr(unsafe.Pointer(guid)), uintptr(unsafe.Pointer(settings))); returnCode != 0 {
		return fmt.Errorf("SetInterfaceDNSSettings returned code: %v and error: %w", windows.Errno(returnCode), err)
	}
	return nil
}

// SetForwardRoute sets the IP forward entry for the given interface.
// https://learn.microsoft.com/en-us/windows/win32/api/netioapi/nf-netioapi-setipforwardentry2
func SetForwardRoute(guid *windows.GUID, settings *MIBIPFORWARDROW2) error {
	if returnCode, _, err := procSetIPForwardEntry.Call(uintptr(unsafe.Pointer(guid)), uintptr(unsafe.Pointer(settings))); returnCode != 0 {
		return fmt.Errorf("SetForwardRoute returned code: %v and error:%w", windows.Errno(returnCode), err)
	}
	return nil
}

// SetInterfaceIPAddress sets the IP address for the given interface.
// https://learn.microsoft.com/en-us/windows/win32/api/netioapi/nf-netioapi-createunicastipaddressentry
func SetInterfaceIPAddress(guid *windows.GUID, settings *MIBUNICASTIPADDRESSROW) error {
	if returnCode, _, err := procCreateUnicastIPAddressEntry.Call(uintptr(unsafe.Pointer(guid)), uintptr(unsafe.Pointer(settings))); returnCode != 0 {
		return fmt.Errorf("CreateUnicastIPAddressEntry returned code: %v and error: %w", windows.Errno(returnCode), err)
	}
	return nil
}

// IPToSockaddrInet is a Helper function to convert a net.IP to a SockaddrInet structure.
func IPToSockaddrInet(ip net.IP) (SockaddrInet, error) {
	var sockaddr SockaddrInet
	ip4 := ip.To4()
	if ip4 != nil {
		sockaddr.Family = windows.AF_INET
		copy(sockaddr.Data[2:6], ip4)
		return sockaddr, nil
	}
	ip6 := ip.To16()
	if ip6 != nil {
		sockaddr.Family = windows.AF_INET6
		copy(sockaddr.Data[6:22], ip6)
		return sockaddr, nil
	}
	return sockaddr, fmt.Errorf("invalid IP address")
}

// ListLocalInterfaces lists local NIC's that match the given flags.
func ListLocalInterfaces(flags GAAFlags) ([]*windows.IpAdapterAddresses, error) {
	var b []byte
	// Recommended initial size: https://learn.microsoft.com/en-us/windows/win32/api/iphlpapi/nf-iphlpapi-getadaptersaddresses#remarks
	l := uint32(15000)
	for {
		b = make([]byte, l)
		// https://learn.microsoft.com/en-us/windows/win32/api/iphlpapi/nf-iphlpapi-getadaptersaddresses
		err := windows.GetAdaptersAddresses(syscall.AF_UNSPEC, uint32(flags), 0, (*windows.IpAdapterAddresses)(unsafe.Pointer(&b[0])), &l)
		if err == nil {
			if l == 0 {
				return nil, nil
			}
			break
		}
		if err.(syscall.Errno) != syscall.ERROR_BUFFER_OVERFLOW {
			return nil, os.NewSyscallError("getadaptersaddresses", err)
		}
		if l <= uint32(len(b)) {
			return nil, os.NewSyscallError("getadaptersaddresses", err)
		}
	}
	var aas []*windows.IpAdapterAddresses
	for aa := (*windows.IpAdapterAddresses)(unsafe.Pointer(&b[0])); aa != nil; aa = aa.Next {
		aas = append(aas, aa)
	}
	return aas, nil
}
