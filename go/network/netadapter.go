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
	"golang.org/x/sys/windows"
	"github.com/go-ole/go-ole"
	"github.com/go-ole/go-ole/oleutil"
)

// NetAdapter represents a MSFT_NetAdapter object. It's important to note that some fields are read-only.
//
// Ref: https://learn.microsoft.com/en-us/previous-versions/windows/desktop/legacy/hh968170(v=vs.85)
type NetAdapter struct {
	// The name of the network adapter. This property is inherited from CIM_ManagedSystemElement.
	Name string
	// Current status of the object. This property is inherited from CIM_ManagedSystemElement.
	Status string
	// The availability and status of the device. This property is inherited from CIM_LogicalDevice.
	Availability uint16
	// If TRUE, the device is using a user-defined configuration. This property is inherited from CIM_LogicalDevice.
	ConfigManagerUserConfig bool
	// The name of the class or subclass used in the creation of an instance. This property is inherited from CIM_LogicalDevice.
	CreationClassName string
	// The address or other identifying information for the network adapter. This property is inherited from CIM_LogicalDevice.
	DeviceID string
	// If TRUE, the error reported in the LastErrorCode property is now cleared. This property is inherited from CIM_LogicalDevice.
	ErrorCleared bool
	// A string that provides more information about the error recorded in the LastErrorCode property and information about any corrective actions that can be taken. This property is inherited from CIM_LogicalDevice.
	ErrorDescription string
	// The last error code reported by the logical device. This property is inherited from CIM_LogicalDevice.
	LastErrorCode uint32
	// The Plug and Play device identifier of the logical device. This property is inherited from CIM_LogicalDevice.
	PNPDeviceID string
	// An array of the specific power-related capabilities of a logical device. This property is inherited from CIM_LogicalDevice.
	PowerManagementCapabilities []uint16
	// If TRUE, the device can be power managed. This property is inherited from CIM_LogicalDevice.
	PowerManagementSupported bool
	// The status of the logical device. This property is inherited from CIM_LogicalDevice.
	StatusInfo uint16
	// The value of the CreationClassName property for the scoping system. This property is inherited from CIM_LogicalDevice.
	SystemCreationClassName string
	// The name of the scoping system. This property is inherited from CIM_LogicalDevice.
	SystemName string
	// The current bandwidth of the port in bits per second.
	Speed uint64
	// The maximum bandwidth of the port in bits per second.
	MaxSpeed uint64
	// The requested bandwidth of the port in bits per second.
	RequestedSpeed uint64
	// In cases where a port can be used for more than one function, this property indicates its primary usage.
	UsageRestriction uint16
	// The specific type of the port.
	PortType uint16
	// A string that describes the port type when the PortType property is set to 1 (Other).
	OtherPortType string
	// The network port type when the PortType property is set to 1 (Other).
	OtherNetworkPortType string
	// The port number.
	PortNumber uint16
	// The link technology for the port.
	LinkTechnology uint16
	// A string that describes the link technology when the LinkTechnology property is set to 1 (Other).
	OtherLinkTechnology string
	// The network address that is hardcoded into a port.
	PermanentAddress string
	// An array of network addresses for the port.
	NetworkAddresses []string
	// If TRUE, the port is operating in full duplex mode.
	FullDuplex bool
	// If TRUE, the port can automatically determine the speed or other communications characteristics of the attached network media.
	AutoSense bool
	// The maximum transmission unit (MTU) that can be supported.
	SupportedMaximumTransmissionUnit uint64
	// The active or negotiated maximum transmission unit (MTU) on the port.
	ActiveMaximumTransmissionUnit uint64
	// The description of the network interface.
	InterfaceDescription string
	// The name of the network interface.
	InterfaceName string
	// The network layer unique identifier (LUID) for the network interface.
	NetLuid uint64
	// The GUID for the network interface.
	InterfaceGUID windows.GUID
	// The index for the network interface.
	InterfaceIndex uint32
	// The name of the device object for the network adapter.
	DeviceName string
	// The index of the LUID for the network adapter.
	NetLuidIndex uint32
	// If TRUE, this is a virtual network adapter.
	Virtual bool
	// If TRUE, this network adapter is not displayed in the user interface.
	Hidden bool
	// If TRUE, this network adapter cannot be removed by a user.
	NotUserRemovable bool
	// If TRUE, this is an intermediate driver filter.
	IMFilter bool
	// The interface type as defined by the Internet Assigned Names Authority (IANA).
	InterfaceType uint32
	// If TRUE, this is a hardware interface.
	HardwareInterface bool
	// If TRUE, this is a WDM interface.
	WdmInterface bool
	// If TRUE, this is an endpoint interface.
	EndPointInterface bool
	// If TRUE, this is an iSCSI interface.
	ISCSIInterface bool
	// The current state of the network adapter.
	State uint32
	// The media type that the network adapter supports.
	NdisMedium uint32
	// The physical media type of the network adapter.
	NdisPhysicalMedium uint32
	// The operational status of the network interface.
	InterfaceOperationalStatus uint32
	// If TRUE, the operational status is down because the default port is not authenticated.
	OperationalStatusDownDefaultPortNotAuthenticated bool
	// If TRUE, the operational status is down because the media is disconnected.
	OperationalStatusDownMediaDisconnected bool
	// If TRUE, the operational status is down because the interface is paused.
	OperationalStatusDownInterfacePaused bool
	// If TRUE, the operational status is down because the interface is in a low power state.
	OperationalStatusDownLowPowerState bool
	// The administrative status of the network interface.
	InterfaceAdminStatus uint32
	// The media connect state of the network adapter.
	MediaConnectState uint32
	// The maximum transmission unit (MTU) size for the network adapter.
	MtuSize uint32
	// The VLAN identifier for the network adapter.
	VlanID uint16
	// The transmit link speed for the network adapter.
	TransmitLinkSpeed uint64
	// The receive link speed for the network adapter.
	ReceiveLinkSpeed uint64
	// If TRUE, the network adapter is in promiscuous mode.
	PromiscuousMode bool
	// If TRUE, the device is enabled to wake the system.
	DeviceWakeUpEnable bool
	// If TRUE, a connector is present on the network adapter.
	ConnectorPresent bool
	// The duplex state of the media.
	MediaDuplexState uint32
	// The date of the driver for the network adapter.
	DriverDate string
	// The date of the driver for the network adapter, in 100-nanosecond intervals.
	DriverDateData uint64
	// The version of the driver for the network adapter.
	DriverVersionString string
	// The name of the driver for the network adapter.
	DriverName string
	// The description of the driver for the network adapter.
	DriverDescription string
	// The major version of the driver for the network adapter.
	MajorDriverVersion uint16
	// The minor version of the driver for the network adapter.
	MinorDriverVersion uint16
	// The major NDIS version of the driver for the network adapter.
	DriverMajorNdisVersion uint8
	// The minor NDIS version of the driver for the network adapter.
	DriverMinorNdisVersion uint8
	// The provider of the driver for the network adapter.
	DriverProvider string
	// The component identifier for the network adapter.
	ComponentID string
	// The indices of the lower layer interfaces.
	LowerLayerInterfaceIndices []uint32
	// The indices of the higher layer interfaces.
	HigherLayerInterfaceIndices []uint32
	// If TRUE, the network adapter is administratively locked.
	AdminLocked bool

	handle *ole.IDispatch
}

// A NetAdapterSet contains one or more NetAdapters.
type NetAdapterSet struct {
	NetAdapters []NetAdapter
}

// Close releases the handle to the network adapter.
func (n *NetAdapter) Close() {
	if n.handle != nil {
		n.handle.Release()
	}
}

// GetNetAdapters queries for local network adapters.
//
// Close() must be called on the resulting NetAdapter to ensure all network adapters are released.
//
// Get all network adapters:
//
//	svc.GetNetAdapters("")
//
// To get specific network adapters, provide a valid WMI query filter string, for example:
//
//	svc.GetNetAdapters("WHERE Name='Wi-Fi'")
func (svc Service) GetNetAdapters(filter string) (NetAdapterSet, error) {
	var netAdapters NetAdapterSet
	query := "SELECT * FROM MSFT_NetAdapter"
	if filter != "" {
		query = fmt.Sprintf("%s %s", query, filter)
	}

	deck.InfoA(query).With(deck.V(1)).Go()
	raw, err := oleutil.CallMethod(svc.wmiSvc, "ExecQuery", query)
	if err != nil {
		return netAdapters, fmt.Errorf("ExecQuery(%s): %w", query, err)
	}
	result := raw.ToIDispatch()
	defer result.Release()

	countVar, err := oleutil.GetProperty(result, "Count")
	if err != nil {
		return netAdapters, fmt.Errorf("oleutil.GetProperty(Count): %w", err)
	}
	count := int(countVar.Val)

	for i := 0; i < count; i++ {
		netAdapter := NetAdapter{}
		itemRaw, err := oleutil.CallMethod(result, "ItemIndex", i)
		if err != nil {
			return netAdapters, fmt.Errorf("oleutil.CallMethod(ItemIndex, %d): %w", i, err)
		}
		netAdapter.handle = itemRaw.ToIDispatch()

		if err := netAdapter.Query(); err != nil {
			return netAdapters, fmt.Errorf("netAdapter.Query(): %w", err)
		}

		netAdapters.NetAdapters = append(netAdapters.NetAdapters, netAdapter)
	}

	return netAdapters, nil
}

// Disable disables the network adapter.
//
// Ref: https://learn.microsoft.com/en-us/windows/win32/fwp/wmi/netadaptercimprov/disable-msft-netadapter
func (n *NetAdapter) Disable() error {
	if n.handle == nil {
		return fmt.Errorf("invalid handle")
	}
	res, err := oleutil.CallMethod(n.handle, "Disable")
	if err != nil {
		return fmt.Errorf("Disable: %w", err)
	}
	if val, ok := res.Value().(int32); val != 0 || !ok {
		return fmt.Errorf("error code returned during Disable: %d", val)
	}
	return nil
}

// Enable enables the network adapter.
//
// Ref: https://learn.microsoft.com/en-us/windows/win32/fwp/wmi/netadaptercimprov/enable-msft-netadapter
func (n *NetAdapter) Enable() error {
	if n.handle == nil {
		return fmt.Errorf("invalid handle")
	}
	res, err := oleutil.CallMethod(n.handle, "Enable")
	if err != nil {
		return fmt.Errorf("Enable: %w", err)
	}
	if val, ok := res.Value().(int32); val != 0 || !ok {
		return fmt.Errorf("error code returned during Enable: %d", val)
	}
	return nil
}

// Rename renames the network adapter.
//
// Ref: https://learn.microsoft.com/en-us/windows/win32/fwp/wmi/netadaptercimprov/msft-netadapter-rename
func (n *NetAdapter) Rename(name string) error {
	if n.handle == nil {
		return fmt.Errorf("invalid handle")
	}
	res, err := oleutil.CallMethod(n.handle, "Rename", name)
	if err != nil {
		return fmt.Errorf("Rename: %w", err)
	}
	if val, ok := res.Value().(int32); val != 0 || !ok {
		return fmt.Errorf("error code returned during Rename: %d", val)
	}
	return nil
}

// Query reads and populates the network adapter state from WMI.
func (n *NetAdapter) Query() error {
	if n.handle == nil {
		return fmt.Errorf("invalid handle")
	}

	// All the non-string/slice properties
	for _, prop := range [][]any{
		{"Availability", &n.Availability},
		{"ErrorCleared", &n.ErrorCleared},
		{"LastErrorCode", &n.LastErrorCode},
		{"PowerManagementSupported", &n.PowerManagementSupported},
		{"StatusInfo", &n.StatusInfo},
		{"Speed", &n.Speed},
		{"MaxSpeed", &n.MaxSpeed},
		{"RequestedSpeed", &n.RequestedSpeed},
		{"UsageRestriction", &n.UsageRestriction},
		{"PortType", &n.PortType},
		{"PortNumber", &n.PortNumber},
		{"LinkTechnology", &n.LinkTechnology},
		{"FullDuplex", &n.FullDuplex},
		{"AutoSense", &n.AutoSense},
		{"SupportedMaximumTransmissionUnit", &n.SupportedMaximumTransmissionUnit},
		{"ActiveMaximumTransmissionUnit", &n.ActiveMaximumTransmissionUnit},
		{"NetLuid", &n.NetLuid},
		{"InterfaceIndex", &n.InterfaceIndex},
		{"NetLuidIndex", &n.NetLuidIndex},
		{"Virtual", &n.Virtual},
		{"Hidden", &n.Hidden},
		{"NotUserRemovable", &n.NotUserRemovable},
		{"IMFilter", &n.IMFilter},
		{"InterfaceType", &n.InterfaceType},
		{"HardwareInterface", &n.HardwareInterface},
		{"WdmInterface", &n.WdmInterface},
		{"EndPointInterface", &n.EndPointInterface},
		{"ISCSIInterface", &n.ISCSIInterface},
		{"State", &n.State},
		{"NdisMedium", &n.NdisMedium},
		{"NdisPhysicalMedium", &n.NdisPhysicalMedium},
		{"InterfaceOperationalStatus", &n.InterfaceOperationalStatus},
		{"OperationalStatusDownDefaultPortNotAuthenticated", &n.OperationalStatusDownDefaultPortNotAuthenticated},
		{"OperationalStatusDownMediaDisconnected", &n.OperationalStatusDownMediaDisconnected},
		{"OperationalStatusDownInterfacePaused", &n.OperationalStatusDownInterfacePaused},
		{"OperationalStatusDownLowPowerState", &n.OperationalStatusDownLowPowerState},
		{"InterfaceAdminStatus", &n.InterfaceAdminStatus},
		{"MediaConnectState", &n.MediaConnectState},
		{"MtuSize", &n.MtuSize},
		{"VlanID", &n.VlanID},
		{"TransmitLinkSpeed", &n.TransmitLinkSpeed},
		{"ReceiveLinkSpeed", &n.ReceiveLinkSpeed},
		{"PromiscuousMode", &n.PromiscuousMode},
		{"DeviceWakeUpEnable", &n.DeviceWakeUpEnable},
		{"ConnectorPresent", &n.ConnectorPresent},
		{"MediaDuplexState", &n.MediaDuplexState},
		{"DriverDateData", &n.DriverDateData},
		{"MajorDriverVersion", &n.MajorDriverVersion},
		{"MinorDriverVersion", &n.MinorDriverVersion},
		{"DriverMajorNdisVersion", &n.DriverMajorNdisVersion},
		{"DriverMinorNdisVersion", &n.DriverMinorNdisVersion},
		{"AdminLocked", &n.AdminLocked},
	} {
		val, err := oleutil.GetProperty(n.handle, prop[0].(string))
		if err != nil {
			return fmt.Errorf("oleutil.GetProperty(%s): %w", prop[0].(string), err)
		}
		if val.VT != ole.VT_NULL {
			if err := AssignVariant(val.Value(), prop[1]); err != nil {
				deck.Warningf("AssignVariant(%s): %v", prop[0].(string), err)
			}
		}
	}

	// String properties
	for _, prop := range [][]any{
		{"Name", &n.Name},
		{"Status", &n.Status},
		{"CreationClassName", &n.CreationClassName},
		{"DeviceID", &n.DeviceID},
		{"ErrorDescription", &n.ErrorDescription},
		{"PNPDeviceID", &n.PNPDeviceID},
		{"SystemCreationClassName", &n.SystemCreationClassName},
		{"SystemName", &n.SystemName},
		{"OtherPortType", &n.OtherPortType},
		{"OtherNetworkPortType", &n.OtherNetworkPortType},
		{"OtherLinkTechnology", &n.OtherLinkTechnology},
		{"PermanentAddress", &n.PermanentAddress},
		{"InterfaceDescription", &n.InterfaceDescription},
		{"InterfaceName", &n.InterfaceName},
		{"DeviceName", &n.DeviceName},
		{"DriverDate", &n.DriverDate},
		{"DriverVersionString", &n.DriverVersionString},
		{"DriverName", &n.DriverName},
		{"DriverDescription", &n.DriverDescription},
		{"DriverProvider", &n.DriverProvider},
		{"ComponentID", &n.ComponentID},
	} {
		val, err := oleutil.GetProperty(n.handle, prop[0].(string))
		if err != nil {
			return fmt.Errorf("oleutil.GetProperty(%s): %w", prop[0].(string), err)
		}
		if val.VT != ole.VT_NULL {
			*(prop[1].(*string)) = val.ToString()
		}
	}

	// GUID
	prop, err := oleutil.GetProperty(n.handle, "InterfaceGUID")
	if err != nil {
		return fmt.Errorf("oleutil.GetProperty(InterfaceGUID): %w", err)
	}
	if prop.VT != ole.VT_NULL {
		guid, err := windows.GUIDFromString(prop.ToString())
		if err != nil {
			return fmt.Errorf("GUIDFromString(%s): %w", prop.ToString(), err)
		}
		n.InterfaceGUID = guid
	}

	// Slice properties
	// NetworkAddresses
	prop, err = oleutil.GetProperty(n.handle, "NetworkAddresses")
	if err != nil {
		return fmt.Errorf("oleutil.GetProperty(NetworkAddresses): %w", err)
	}
	if prop.VT != ole.VT_NULL {
		for _, v := range prop.ToArray().ToValueArray() {
			s, ok := v.(string)
			if !ok {
				return fmt.Errorf("error converting NetworkAddress to string")
			}
			n.NetworkAddresses = append(n.NetworkAddresses, s)
		}
	}

	// PowerManagementCapabilities
	prop, err = oleutil.GetProperty(n.handle, "PowerManagementCapabilities")
	if err != nil {
		return fmt.Errorf("oleutil.GetProperty(PowerManagementCapabilities): %w", err)
	}
	if prop.VT != ole.VT_NULL {
		for _, v := range prop.ToArray().ToValueArray() {
			val, ok := v.(int32)
			if !ok {
				return fmt.Errorf("error converting PowerManagementCapabilities to uint16, got %T", v)
			}
			n.PowerManagementCapabilities = append(n.PowerManagementCapabilities, uint16(val))
		}
	}

	// LowerLayerInterfaceIndices
	prop, err = oleutil.GetProperty(n.handle, "LowerLayerInterfaceIndices")
	if err != nil {
		return fmt.Errorf("oleutil.GetProperty(LowerLayerInterfaceIndices): %w", err)
	}
	if prop.VT != ole.VT_NULL {
		for _, v := range prop.ToArray().ToValueArray() {
			val, ok := v.(int32)
			if !ok {
				return fmt.Errorf("error converting LowerLayerInterfaceIndices to uint32, got %T", v)
			}
			n.LowerLayerInterfaceIndices = append(n.LowerLayerInterfaceIndices, uint32(val))
		}
	}

	// HigherLayerInterfaceIndices
	prop, err = oleutil.GetProperty(n.handle, "HigherLayerInterfaceIndices")
	if err != nil {
		return fmt.Errorf("oleutil.GetProperty(HigherLayerInterfaceIndices): %w", err)
	}
	if prop.VT != ole.VT_NULL {
		for _, v := range prop.ToArray().ToValueArray() {
			val, ok := v.(int32)
			if !ok {
				return fmt.Errorf("error converting HigherLayerInterfaceIndices to uint32, got %T", v)
			}
			n.HigherLayerInterfaceIndices = append(n.HigherLayerInterfaceIndices, uint32(val))
		}
	}

	return nil
}
