// Copyright 2025 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//	http://www.apache.org/licenses/LICENSE-2.0
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
	"github.com/scjalliance/comshim"
	"github.com/go-ole/go-ole"
	"github.com/go-ole/go-ole/oleutil"
)

// Service represents a connection to the host Storage service (in WMI).
type Service struct {
	wmiIntf *ole.IDispatch
	wmiSvc  *ole.IDispatch
}

// AdapterConnect connects to the WMI provider for managing network adapter objects.
// You must call Close() to release the provider when finished.
//
// Example: network.AdapterConnect()
func AdapterConnect() (Service, error) {
	comshim.Add(1)
	svc := Service{}

	unknown, err := oleutil.CreateObject("WbemScripting.SWbemLocator")
	if err != nil {
		comshim.Done()
		return svc, fmt.Errorf("CreateObject: %w", err)
	}
	defer unknown.Release()
	svc.wmiIntf, err = unknown.QueryInterface(ole.IID_IDispatch)
	if err != nil {
		comshim.Done()
		return svc, fmt.Errorf("QueryInterface: %w", err)
	}
	serviceRaw, err := oleutil.CallMethod(svc.wmiIntf, "ConnectServer", nil)
	if err != nil {
		svc.Close()
		return svc, fmt.Errorf("ConnectServer: %w", err)
	}
	svc.wmiSvc = serviceRaw.ToIDispatch()

	return svc, nil
}

// AdapterConfiguration represents a Win32_NetworkAdapterConfiguration object.
//
// Ref: https://learn.microsoft.com/en-us/previous-versions/windows/desktop/legacy/hh968170(v=vs.85)
type AdapterConfiguration struct {
	Caption              string
	Description          string
	DHCPEnabled          bool
	DHCPServer           string
	DNSDomain            string
	DNSHostName          string
	DNSServerSearchOrder []string
	IPAddress            []string
	IPEnabled            bool
	IPSubnet             []string
	MACAddress           string
	DefaultIPGateway     []string
	ServiceName          string
	SettingID            string
	InterfaceIndex       uint32

	handle *ole.IDispatch
}

// An AdapterConfigurationSet contains one or more NetworkAdapterConfigurations.
type AdapterConfigurationSet struct {
	NetworkAdapterConfigurations []AdapterConfiguration
}

// GetNetworkAdapterConfigurations returns an AdapterConfigurationSet.
func (svc Service) GetNetworkAdapterConfigurations(filter string) (AdapterConfigurationSet, error) {
	var configs AdapterConfigurationSet
	query := "SELECT * FROM Win32_NetworkAdapterConfiguration"
	if filter != "" {
		query = fmt.Sprintf("%s %s", query, filter)
	}

	deck.InfoA(query).With(deck.V(1)).Go()
	raw, err := oleutil.CallMethod(svc.wmiSvc, "ExecQuery", query)
	if err != nil {
		return configs, fmt.Errorf("ExecQuery(%s): %w", query, err)
	}
	result := raw.ToIDispatch()
	defer result.Release()

	countVar, err := oleutil.GetProperty(result, "Count")
	if err != nil {
		return configs, fmt.Errorf("oleutil.GetProperty(Count): %w", err)
	}
	count := int(countVar.Val)

	for i := 0; i < count; i++ {
		config := AdapterConfiguration{}
		itemRaw, err := oleutil.CallMethod(result, "ItemIndex", i)
		if err != nil {
			return configs, fmt.Errorf("oleutil.CallMethod(ItemIndex, %d): %w", i, err)
		}
		config.handle = itemRaw.ToIDispatch()

		if err := config.Query(); err != nil {
			return configs, err
		}

		configs.NetworkAdapterConfigurations = append(configs.NetworkAdapterConfigurations, config)
	}

	return configs, nil
}

// Query reads and populates the network adapter state from WMI.
func (n *AdapterConfiguration) Query() error {
	if n.handle == nil {
		return fmt.Errorf("invalid handle")
	}

	// Non-string/slice properties
	for _, prop := range [][]any{
		{"DHCPEnabled", &n.DHCPEnabled},
		{"IPEnabled", &n.IPEnabled},
		{"InterfaceIndex", &n.InterfaceIndex},
	} {
		name, ok := prop[0].(string)
		if !ok {
			return fmt.Errorf("failed to convert property name to string: %v", prop[0])
		}
		val, err := oleutil.GetProperty(n.handle, name)
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
		{"Caption", &n.Caption},
		{"Description", &n.Description},
		{"DHCPServer", &n.DHCPServer},
		{"DNSDomain", &n.DNSDomain},
		{"DNSHostName", &n.DNSHostName},
		{"MACAddress", &n.MACAddress},
		{"ServiceName", &n.ServiceName},
		{"SettingID", &n.SettingID},
	} {
		name, ok := prop[0].(string)
		if !ok {
			return fmt.Errorf("failed to convert property name to string: %v", prop[0])
		}
		val, err := oleutil.GetProperty(n.handle, name)
		if err != nil {
			return fmt.Errorf("oleutil.GetProperty(%s): %w", name, err)
		}
		if val.VT != ole.VT_NULL {
			*(prop[1].(*string)) = val.ToString()
		}
	}

	// Slice properties
	for _, sliceProp := range []struct {
		Name string
		Dst  *[]string
	}{
		{"DNSServerSearchOrder", &n.DNSServerSearchOrder},
		{"IPAddress", &n.IPAddress},
		{"IPSubnet", &n.IPSubnet},
		{"DefaultIPGateway", &n.DefaultIPGateway},
	} {
		prop, err := oleutil.GetProperty(n.handle, sliceProp.Name)
		if err != nil {
			deck.Warningf("oleutil.GetProperty(%s): %v", sliceProp.Name, err)
			continue
		}
		if prop.VT != ole.VT_NULL {
			for _, v := range prop.ToArray().ToValueArray() {
				s, ok := v.(string)
				if !ok {
					deck.Warningf("error converting %s to string", sliceProp.Name)
				} else {
					*sliceProp.Dst = append(*sliceProp.Dst, s)
				}
			}
		}
	}

	return nil
}

// StaticRoute sets the static route for the network adapter.
//
// IMPORTANT: This method ONLY supports Ipv4.
//
// Ref: https://learn.microsoft.com/en-us/windows/win32/cimwin32prov/enablestatic-method-in-class-win32-networkadapterconfiguration
func (n *AdapterConfiguration) StaticRoute(ipaddress []string, subnetMask []string) error {
	res, err := oleutil.CallMethod(n.handle, "EnableStatic", ipaddress, subnetMask)
	if err != nil {
		return fmt.Errorf("EnableStatic: %w", err)
	}
	if val, ok := res.Value().(int32); val != 0 || !ok {
		return fmt.Errorf("error code returned during EnableStatic: %d", val)
	}
	return nil
}
