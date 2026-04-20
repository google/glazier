// Copyright 2025 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License")
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

package netw

import (
	"fmt"

	"github.com/google/deck"
	"github.com/go-ole/go-ole"
	"github.com/go-ole/go-ole/oleutil"
)

// IPAddress represents a MSFT_NetIPAddress object.
//
// Ref: https://learn.microsoft.com/en-us/windows/win32/fwp/wmi/nettcpipprov/msft-netipaddress
type IPAddress struct {
	AddressFamily     uint16
	AddressState      uint16
	InterfaceAlias    string
	InterfaceIndex    uint32
	IPAddress         string
	PreferredLifetime string
	PrefixOrigin      uint16
	SkipAsSource      bool
	Store             uint8
	SuffixOrigin      uint16
	Type              uint8
	ValidLifetime     string

	// handle is the internal ole handle
	handle *ole.IDispatch
}

// CreateIPAddressOptions represents the options for creating an IP address.
//
// Ref: https://learn.microsoft.com/en-us/windows/win32/fwp/wmi/nettcpipprov/create-msft-netipaddress
type CreateIPAddressOptions struct {
	InterfaceIndex    uint32
	InterfaceAlias    string
	IPAddress         string
	AddressFamily     uint16
	PrefixLength      uint8
	Type              uint8
	PrefixOrigin      uint8
	SuffixOrigin      uint8
	AddressState      uint16
	ValidLifetime     string // CIM_DATETIME
	PreferredLifetime string // CIM_DATETIME
	SkipAsSource      bool
	DefaultGateway    string
	PolicyStore       string
	PassThru          bool
}

// IPAddressSet contains one or more IPAddresses.
type IPAddressSet struct {
	IPAddresses []IPAddress
}

// GetIPAddresses returns a IPAddresses struct.
//
// Get all IP addresses:
//
//	svc.GetIPAddresses("")
//
// To get specific IP addresses, provide a valid WMI query filter string, for example:
//
//	svc.GetIPAddresses("WHERE IPAddress='192.168.1.1'")
func (svc Service) GetIPAddresses(filter string) (IPAddressSet, error) {
	var ipset IPAddressSet
	query := "SELECT * FROM MSFT_NetIPAddress"
	if filter != "" {
		query = fmt.Sprintf("%s %s", query, filter)
	}

	deck.InfoA(query).With(deck.V(1)).Go()
	raw, err := oleutil.CallMethod(svc.wmiSvc, "ExecQuery", query)
	if err != nil {
		return ipset, fmt.Errorf("ExecQuery(%s): %w", query, err)
	}
	result := raw.ToIDispatch()
	defer result.Release()

	countVar, err := oleutil.GetProperty(result, "Count")
	if err != nil {
		return ipset, fmt.Errorf("oleutil.GetProperty(Count): %w", err)
	}
	count := int(countVar.Val)

	for i := 0; i < count; i++ {
		ipresult := IPAddress{}
		itemRaw, err := oleutil.CallMethod(result, "ItemIndex", i)
		if err != nil {
			return ipset, fmt.Errorf("oleutil.CallMethod(ItemIndex, %d): %w", i, err)
		}
		ipresult.handle = itemRaw.ToIDispatch()

		if err := ipresult.Query(); err != nil {
			return ipset, fmt.Errorf("ipresult.Query(): %w", err)
		}

		ipset.IPAddresses = append(ipset.IPAddresses, ipresult)
	}

	return ipset, nil
}

// Close releases the handle to the IP address.
func (ip *IPAddress) Close() {
	if ip.handle != nil {
		ip.handle.Release()
	}
}

// Query reads and populates the IP address state from WMI.
func (ip *IPAddress) Query() error {
	if ip.handle == nil {
		return fmt.Errorf("invalid handle")
	}

	// All the non-string/slice properties
	for _, prop := range [][]any{
		{"AddressFamily", &ip.AddressFamily},
		{"InterfaceIndex", &ip.InterfaceIndex},
		{"PrefixOrigin", &ip.PrefixOrigin},
		{"SkipAsSource", &ip.SkipAsSource},
		{"SuffixOrigin", &ip.SuffixOrigin},
		{"Type", &ip.Type},
		{"Store", &ip.Store},
		{"AddressState", &ip.AddressState},
	} {
		name, ok := prop[0].(string)
		if !ok {
			return fmt.Errorf("failed to convert property name to string: %v", prop[0])
		}
		val, err := oleutil.GetProperty(ip.handle, name)
		if err != nil {
			return fmt.Errorf("oleutil.GetProperty(%s): %w", name, err)
		}
		if val.VT != ole.VT_NULL {
			if err := AssignVariant(val.Value(), prop[1]); err != nil {
				deck.Warningf("AssignVariant(%s): %v", name, err)
			}
		}
	}

	// String properties
	for _, prop := range [][]any{
		{"InterfaceAlias", &ip.InterfaceAlias},
		{"IPAddress", &ip.IPAddress},
		{"ValidLifetime", &ip.ValidLifetime},
		{"PreferredLifetime", &ip.PreferredLifetime},
	} {
		name, ok := prop[0].(string)
		if !ok {
			return fmt.Errorf("failed to convert property name to string: %v", prop[0])
		}
		val, err := oleutil.GetProperty(ip.handle, name)
		if err != nil {
			return fmt.Errorf("oleutil.GetProperty(%s): %w", name, err)
		}
		if val.VT != ole.VT_NULL {
			*(prop[1].(*string)) = val.ToString()
		}
	}

	return nil
}

// IPOutput represents the output of the Create method.
type IPOutput struct{}

// Create creates the IP address on the current instance.
//
// Ref: https://learn.microsoft.com/en-us/windows/win32/fwp/wmi/nettcpipprov/create-msft-netipaddress
func (ip *IPAddress) Create(opts CreateIPAddressOptions) (IPOutput, error) {
	ipset := IPOutput{}

	return ipset, fmt.Errorf("not implemented")

	// var createdObject ole.VARIANT
	// ole.VariantInit(&createdObject)

	// Parameters must be passed in the order defined by the WMI method signature.
	//	res, err := oleutil.CallMethod(ip.handle, "Create",
	//  opts.InterfaceIndex,
	//  opts.InterfaceAlias,
	//  opts.IPAddress,
	//	opts.AddressFamily,
	//	opts.PrefixLength,
	//	opts.Type,
	//	opts.PrefixOrigin,
	//	opts.SuffixOrigin,
	//	opts.AddressState,
	//	opts.ValidLifetime,
	//	opts.PreferredLifetime,
	//	opts.SkipAsSource,
	//	opts.DefaultGateway,
	//	opts.PolicyStore,
	//	opts.PassThru,
	//	&createdObject, // output
	// )
	// if err != nil {
	//	return ipset, fmt.Errorf("Create: %w", err)
	// }
	// if val, ok := res.Value().(int32); val != 0 || !ok {
	//	return ipset, fmt.Errorf("error code returned during create: %d", val)
	// }

	//	ip.handle = createdObject.ToIDispatch()

	// return ipset, nil
}
