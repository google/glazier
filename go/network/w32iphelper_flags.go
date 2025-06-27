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

// GAAFlags enumeration defines flags used in GetAdaptersAddresses calls
// https://docs.microsoft.com/en-us/windows/desktop/api/iphlpapi/nf-iphlpapi-getadaptersaddresses
type GAAFlags uint32

// https://docs.microsoft.com/en-us/windows/desktop/api/iphlpapi/nf-iphlpapi-getadaptersaddresses
const (
	// GAAFlagSkipUnicast is a flag to skip unicast adapters.
	GAAFlagSkipUnicast = 0x01
	// GAAFlagSkipAnycast is a flag to skip anycast adapters.
	GAAFlagSkipAnycast = 0x02
	// GAAFlagSkipMulticast is a flag to skip multicast adapters.
	GAAFlagSkipMulticast = 0x04
	// GAAFlagSkipDNSServer is a flag to skip DNS server adapters.
	GAAFlagSkipDNSServer = 0x08
	// GAAFlagIncludePrefix is a flag to include prefix information.
	GAAFlagIncludePrefix = 0x10
	// GAAFlagSkipFriendlyName is a flag to skip friendly name information.
	GAAFlagSkipFriendlyName = 0x20
	// GAAFlagIncludeWinsInfo is a flag to include Windows information.
	GAAFlagIncludeWinsInfo = 0x40
	// GAAFlagIncludeGateways is a flag to include gateway information.
	GAAFlagIncludeGateways = 0x80
	// GAAFlagIncludeAllInterfaces is a flag to include all interfaces.
	GAAFlagIncludeAllInterfaces = 0x100
	// GAAFlagIncludeAllCompartments is a flag to include all compartments.
	GAAFlagIncludeAllCompartments = 0x200
	// GAAFlagIncludeTunnelBindingOrder is a flag to include tunnel binding order.
	GAAFlagIncludeTunnelBindingOrder = 0x400
)

// DNSFlags enumeration defines flags used in SetInterfaceDnsSettings calls
// https://learn.microsoft.com/en-us/windows/win32/api/netioapi/nf-netioapi-setinterfacednssettings
type DNSFlags uint32

// https://learn.microsoft.com/en-us/windows/win32/api/netioapi/nf-netioapi-setinterfacednssettings
const (
	// DNSInterfaceSettingsVersion1 is the version 1 of the DnsInterfaceSettings structure.
	DNSInterfaceSettingsVersion1 = 1 // for DnsInterfaceSettings
	// DNSInterfaceSettingsVersion2 is the version 2 of the DnsInterfaceSettings structure.
	DNSInterfaceSettingsVersion2 = 2 // for DnsInterfaceSettings
	// DNSInterfaceSettingsVersion3 is the version 3 of the DnsInterfaceSettings structure.
	DNSInterfaceSettingsVersion3 = 3 // for DnsInterfaceSettings
	// DNSInterfaceSettingsFlagIPv6 is the flag for IPv6 DNS.
	DNSInterfaceSettingsFlagIPv6 = 0x0001
	// DNSInterfaceSettingsFlagNameserver is the flag for nameserver.
	DNSInterfaceSettingsFlagNameserver = 0x0002
	// DNSInterfaceSettingsFlagSearchList is the flag for search list.
	DNSInterfaceSettingsFlagSearchList = 0x0004
	// DNSInterfaceSettingsFlagRegistrationEnabled is the flag for registration enabled.
	DNSInterfaceSettingsFlagRegistrationEnabled = 0x0008
	// DNSInterfaceSettingsFlagRegisterAdapterName is the flag for register adapter name.
	DNSInterfaceSettingsFlagRegisterAdapterName = 0x0010
	// DNSInterfaceSettingsFlagDomain is the flag for domain.
	DNSInterfaceSettingsFlagDomain = 0x0020
	// DNSInterfaceSettingsFlagHostname is the flag for hostname.
	DNSInterfaceSettingsFlagHostname = 0x0040
	// DNSInterfaceSettingsFlagEnableLLMNR is the flag for enable LLMNR.
	DNSInterfaceSettingsFlagEnableLLMNR = 0x0080
	// DNSInterfaceSettingsFlagQueryAdapterName is the flag for query adapter name.
	DNSInterfaceSettingsFlagQueryAdapterName = 0x0100
	// DNSInterfaceSettingsFlagProfileNameserver is the flag for profile nameserver.
	DNSInterfaceSettingsFlagProfileNameserver = 0x0200
	// DNSInterfaceSettingsFlagDisableUnconstrainedQueries is the flag for disabling unconstrained queries.
	DNSInterfaceSettingsFlagDisableUnconstrainedQueries = 0x0400 // v2 only
	// DNSInterfaceSettingsFlagSupplementalSearchList is the flag for supplemental search list.
	DNSInterfaceSettingsFlagSupplementalSearchList = 0x0800 // v2 only
	// DNSInterfaceSettingsFlagDOH is the flag for DNS over HTTP.
	DNSInterfaceSettingsFlagDOH = 0x1000 // v3 only
	// DNSInterfaceSettingsFlagDOHProfile is the flag for DNS over HTTP profile.
	DNSInterfaceSettingsFlagDOHProfile = 0x2000 // v3 only
)
