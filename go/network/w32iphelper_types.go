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

package w32iphelper

// DNSInterfaceSettings is meant to be used with SetInterfaceDnsSettings
// https://learn.microsoft.com/en-us/windows/win32/api/netioapi/nf-netioapi-getinterfacednssettings
type DNSInterfaceSettings struct {
	Version             uint32
	Flags               DNSFlags
	Domain              *uint16
	NameServer          *uint16
	SearchList          *uint16
	RegistrationEnabled uint32
	RegisterAdapterName uint32
	EnableLLMNR         uint32
	QueryAdapterName    uint32
	ProfileNameServer   *uint16
}

// MIBIPFORWARDROW2 stores information about an IP route entry.
// https://learn.microsoft.com/en-us/windows/win32/api/netioapi/ns-netioapi-mib_ipforward_row2
type MIBIPFORWARDROW2 struct {
	InterfaceLuid        uint64
	InterfaceIndex       uint32
	DestinationPrefix    IPAddressPrefix
	NextHop              SockaddrInet
	SitePrefixLength     uint8
	ValidLifetime        uint32
	PreferredLifetime    uint32
	Metric               uint32
	Protocol             RouteProtocol
	Loopback             uint8
	AutoconfigureAddress uint8
	Publish              uint8
	Immortal             uint8
	Origin               uint32
}

// MIBUNICASTIPADDRESSROW is the Go equivalent of the Windows structure.
// https://learn.microsoft.com/en-us/windows/win32/api/netioapi/ns-netioapi-mib_unicastipaddress_row
type MIBUNICASTIPADDRESSROW struct {
	// Address is the IP address of the interface.
	Address SockaddrInet
	// InterfaceLuid is the unique identifier of the interface.
	InterfaceLuid uint64
	// InterfaceIndex is the index of the interface.
	InterfaceIndex uint32
	// PrefixOrigin is the origin of the prefix.
	PrefixOrigin uint8 // NL_PREFIX_ORIGIN
	// SuffixOrigin is the origin of the suffix.
	SuffixOrigin uint8 // NL_SUFFIX_ORIGIN
	// ValidLifetime is the lifetime of the prefix.
	ValidLifetime uint32
	// PreferredLifetime is the lifetime of the prefix.
	PreferredLifetime uint32
	// OnLinkPrefixLength is the length of the prefix.
	OnLinkPrefixLength uint8
	// SkipAsSource is the flag to skip the address as a source.
	SkipAsSource uint8
	// DadState is the DAD state of the prefix.
	DadState uint8 // NL_DAD_STATE
	// ScopeID is the scope of the prefix.
	ScopeID uint32
	// CreateTimestamp is the timestamp of the prefix creation.
	CreateTimestamp int64
}

// RouteProtocol is the protocol of the route entry.
// https://learn.microsoft.com/en-us/windows/win32/api/nldef/ne-nldef-nl_route_protocol
type RouteProtocol uint32

const (
	// MibIPProtoOther means that the routing mechanism was not specified.
	MibIPProtoOther RouteProtocol = 1
	// MibIPProtoLocal is a local interface.
	MibIPProtoLocal RouteProtocol = 2
	// MibIPProtoNetMgmt is a static route.
	MibIPProtoNetMgmt RouteProtocol = 3 // DHCP, static, default gateway etc.
	// MibIPProtoICMP is an ICMP protocol.
	MibIPProtoICMP RouteProtocol = 4
	// MibIPProtoEGP is an EGP protocol.
	MibIPProtoEGP RouteProtocol = 5
	// MibIPProtoGGP is a GGP protocol.
	MibIPProtoGGP RouteProtocol = 6
	// MibIPProtoHELLO is a Hello protocol.
	MibIPProtoHELLO RouteProtocol = 7
	// MibIPProtoRIP is a RIP protocol.
	MibIPProtoRIP RouteProtocol = 8
	// MibIPProtoISIS is an IS-IS protocol.
	MibIPProtoISIS RouteProtocol = 9
	// MibIPProtoESIS is an ES-IS protocol.
	MibIPProtoESIS RouteProtocol = 10
	// MibIPProtoCisco is a Cisco protocol.
	MibIPProtoCisco RouteProtocol = 11
	// MibIPProtoBBN is a BBN protocol.
	MibIPProtoBBN RouteProtocol = 12
	// MibIPProtoOSPF is an OSPF protocol.
	MibIPProtoOSPF RouteProtocol = 13
	// MibIPProtoBGP is a BGP protocol.
	MibIPProtoBGP RouteProtocol = 14
	// MibIPProtoNTAutoStatic is a NT protocol.
	MibIPProtoNTAutoStatic RouteProtocol = 10002
	// MibIPProtoNTStatic is an NT protocol.
	MibIPProtoNTStatic RouteProtocol = 10006
	// MibIPProtoNTStaticNonDOD is an NT protocol.
	MibIPProtoNTStaticNonDOD RouteProtocol = 10007
)

// IPAddressPrefix represents an IP address prefix and its length.
// https://learn.microsoft.com/en-us/windows/win32/api/netioapi/ns-netioapi-ip_address_prefix
type IPAddressPrefix struct {
	Prefix       SockaddrInet
	PrefixLength uint8
}

// SockaddrInet can hold either an IPv4 or IPv6 socket address.
// https://learn.microsoft.com/en-us/windows/win32/api/ws2ipdef/ns-ws2ipdef-sockaddr_inet
type SockaddrInet struct {
	Family uint16 // windows.AF_INET / AF_INET6
	Data   [26]byte
}
