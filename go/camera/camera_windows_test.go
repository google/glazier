//go:build windows
// +build windows

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

package camera

import (
	"errors"
	"strings"
	"syscall"
	"testing"
	"unsafe"

	"golang.org/x/sys/windows"
)

func TestListCameras_Success(t *testing.T) {
	origCoInit := coInitializeEx
	origCoUninit := coUninitialize
	origMFStart := mfStartup
	origMFShut := mfShutdown
	origMFCreateAttr := mfCreateAttributes
	origMFEnum := mfEnumDeviceSources
	origCoFree := coTaskMemFree
	origRelease := comRelease
	origSetGUID := comSetGUID
	origGetAllocString := comGetAllocatedString
	origGetUINT32 := comGetUINT32
	origGetGUID := comGetGUID
	t.Cleanup(func() {
		coInitializeEx = origCoInit
		coUninitialize = origCoUninit
		mfStartup = origMFStart
		mfShutdown = origMFShut
		mfCreateAttributes = origMFCreateAttr
		mfEnumDeviceSources = origMFEnum
		coTaskMemFree = origCoFree
		comRelease = origRelease
		comSetGUID = origSetGUID
		comGetAllocatedString = origGetAllocString
		comGetUINT32 = origGetUINT32
		comGetGUID = origGetGUID
	})

	coInitializeEx = func(uintptr, uint32) error { return nil }
	coUninitialize = func() {}
	mfStartup = func(uint32, uint32) error { return nil }
	mfShutdown = func() error { return nil }
	coTaskMemFree = func(unsafe.Pointer) {}
	comRelease = func(*comObject) {}
	comSetGUID = func(*comObject, *windows.GUID, *windows.GUID) error {
		return nil
	}

	mockAttrCOM := &comObject{}
	mfCreateAttributes = func(ppMFAttributes **comObject, cInitialSize uint32) error {
		*ppMFAttributes = mockAttrCOM
		return nil
	}

	mockActivateCOM := &comObject{}
	devicesArray := []*comObject{mockActivateCOM}

	mfEnumDeviceSources = func(pAttributes *comObject, pppSourceActivate ***comObject, pcSourceActivate *uint32) int32 {
		*pcSourceActivate = 1
		*pppSourceActivate = &devicesArray[0]
		return 0
	}

	comGetAllocatedString = func(c *comObject, key *windows.GUID) (string, error) {
		if *key == guidMFDevSourceAttributeFriendlyName {
			return "Intel(R) MTL AVStream Camera", nil
		}
		if *key == guidMFDevSourceAttributeVidCapSymbolicLink {
			return `\\?\display#intc1070#...`, nil
		}
		return "", errors.New("not implemented")
	}
	comGetUINT32 = func(c *comObject, key *windows.GUID) (uint32, error) {
		return 1, nil
	}
	comGetGUID = func(c *comObject, key *windows.GUID) (windows.GUID, error) {
		return ksCategoryVideoCamera, nil
	}

	cameras, err := ListCameras()
	if err != nil {
		t.Fatalf("ListCameras() error = %v, want nil", err)
	}

	if len(cameras) != 1 {
		t.Fatalf("len(cameras) = %d, want 1", len(cameras))
	}

	cam := cameras[0]
	if cam.Name != "Intel(R) MTL AVStream Camera" {
		t.Errorf("cam.Name = %q, want %q", cam.Name, "Intel(R) MTL AVStream Camera")
	}
	if !cam.IsMIPI {
		t.Errorf("cam.IsMIPI = false, want true")
	}
	if !cam.HardwareSource {
		t.Errorf("cam.HardwareSource = false, want true")
	}
}

func TestListCameras_ZeroDevicesReturns0xA00F4244(t *testing.T) {
	origCoInit := coInitializeEx
	origCoUninit := coUninitialize
	origMFStart := mfStartup
	origMFShut := mfShutdown
	origMFCreateAttr := mfCreateAttributes
	origMFEnum := mfEnumDeviceSources
	origCoFree := coTaskMemFree
	t.Cleanup(func() {
		coInitializeEx = origCoInit
		coUninitialize = origCoUninit
		mfStartup = origMFStart
		mfShutdown = origMFShut
		mfCreateAttributes = origMFCreateAttr
		mfEnumDeviceSources = origMFEnum
		coTaskMemFree = origCoFree
	})

	coInitializeEx = func(uintptr, uint32) error { return nil }
	coUninitialize = func() {}
	mfStartup = func(uint32, uint32) error { return nil }
	mfShutdown = func() error { return nil }
	coTaskMemFree = func(unsafe.Pointer) {}

	var attrVtbl [50]uintptr
	attrVtbl[2] = syscall.NewCallback(func(this uintptr) uintptr { return 1 })
	attrVtbl[24] = syscall.NewCallback(func(this, pKey, pVal uintptr) uintptr { return 0 })
	mockAttrCOM := &comObject{vtbl: &attrVtbl}

	mfCreateAttributes = func(ppMFAttributes **comObject, cInitialSize uint32) error {
		*ppMFAttributes = mockAttrCOM
		return nil
	}

	mfEnumDeviceSources = func(pAttributes *comObject, pppSourceActivate ***comObject, pcSourceActivate *uint32) int32 {
		*pcSourceActivate = 0
		*pppSourceActivate = nil
		return 0
	}

	cameras, err := ListCameras()
	if err == nil {
		t.Fatalf("ListCameras() returned %v, want ErrNoCamerasAttached", cameras)
	}

	if !errors.Is(err, ErrNoCamerasAttached) && !IsNoCamerasAttachedError(err) {
		t.Errorf("ListCameras() err = %v, want ErrNoCamerasAttached (0xA00F4244)", err)
	}
}

func TestListCameras_MFEnumDeviceSourcesErrorReturns0xA00F4244(t *testing.T) {
	origCoInit := coInitializeEx
	origCoUninit := coUninitialize
	origMFStart := mfStartup
	origMFShut := mfShutdown
	origMFCreateAttr := mfCreateAttributes
	origMFEnum := mfEnumDeviceSources
	origCoFree := coTaskMemFree
	t.Cleanup(func() {
		coInitializeEx = origCoInit
		coUninitialize = origCoUninit
		mfStartup = origMFStart
		mfShutdown = origMFShut
		mfCreateAttributes = origMFCreateAttr
		mfEnumDeviceSources = origMFEnum
		coTaskMemFree = origCoFree
	})

	coInitializeEx = func(uintptr, uint32) error { return nil }
	coUninitialize = func() {}
	mfStartup = func(uint32, uint32) error { return nil }
	mfShutdown = func() error { return nil }
	coTaskMemFree = func(unsafe.Pointer) {}

	var attrVtbl [50]uintptr
	attrVtbl[2] = syscall.NewCallback(func(this uintptr) uintptr { return 1 })
	attrVtbl[24] = syscall.NewCallback(func(this, pKey, pVal uintptr) uintptr { return 0 })
	mockAttrCOM := &comObject{vtbl: &attrVtbl}

	mfCreateAttributes = func(ppMFAttributes **comObject, cInitialSize uint32) error {
		*ppMFAttributes = mockAttrCOM
		return nil
	}

	mfEnumDeviceSources = func(pAttributes *comObject, pppSourceActivate ***comObject, pcSourceActivate *uint32) int32 {
		return HResultNoCamerasAttached
	}

	_, err := ListCameras()
	if !IsNoCamerasAttachedError(err) {
		t.Errorf("ListCameras() err = %v, want 0xA00F4244", err)
	}
}

func TestDiagnose_HealthyCamera(t *testing.T) {
	origCoInit := coInitializeEx
	origCoUninit := coUninitialize
	origMFStart := mfStartup
	origMFShut := mfShutdown
	origMFCreateAttr := mfCreateAttributes
	origMFEnum := mfEnumDeviceSources
	origCoFree := coTaskMemFree
	origCMGetIface := cmGetDeviceInterfaceList
	origRelease := comRelease
	origSetGUID := comSetGUID
	origGetAllocString := comGetAllocatedString
	origGetUINT32 := comGetUINT32
	origGetGUID := comGetGUID
	t.Cleanup(func() {
		coInitializeEx = origCoInit
		coUninitialize = origCoUninit
		mfStartup = origMFStart
		mfShutdown = origMFShut
		mfCreateAttributes = origMFCreateAttr
		mfEnumDeviceSources = origMFEnum
		coTaskMemFree = origCoFree
		cmGetDeviceInterfaceList = origCMGetIface
		comRelease = origRelease
		comSetGUID = origSetGUID
		comGetAllocatedString = origGetAllocString
		comGetUINT32 = origGetUINT32
		comGetGUID = origGetGUID
	})

	coInitializeEx = func(uintptr, uint32) error { return nil }
	coUninitialize = func() {}
	mfStartup = func(uint32, uint32) error { return nil }
	mfShutdown = func() error { return nil }
	coTaskMemFree = func(unsafe.Pointer) {}
	comRelease = func(*comObject) {}
	comSetGUID = func(*comObject, *windows.GUID, *windows.GUID) error {
		return nil
	}

	mockAttrCOM := &comObject{}
	mfCreateAttributes = func(ppMFAttributes **comObject, cInitialSize uint32) error {
		*ppMFAttributes = mockAttrCOM
		return nil
	}

	mockActivateCOM := &comObject{}
	devicesArray := []*comObject{mockActivateCOM}

	mfEnumDeviceSources = func(pAttributes *comObject, pppSourceActivate ***comObject, pcSourceActivate *uint32) int32 {
		*pcSourceActivate = 1
		*pppSourceActivate = &devicesArray[0]
		return 0
	}

	comGetAllocatedString = func(c *comObject, key *windows.GUID) (string, error) {
		if *key == guidMFDevSourceAttributeFriendlyName {
			return "Integrated Camera", nil
		}
		if *key == guidMFDevSourceAttributeVidCapSymbolicLink {
			return `\\?\usb#vid_04f2&pid_b6d9#...`, nil
		}
		return "", errors.New("not implemented")
	}
	comGetUINT32 = func(c *comObject, key *windows.GUID) (uint32, error) {
		return 1, nil
	}
	comGetGUID = func(c *comObject, key *windows.GUID) (windows.GUID, error) {
		return ksCategoryVideoCamera, nil
	}

	cmGetDeviceInterfaceList = func(deviceID string, ifaceClass *windows.GUID, flags uint32) ([]string, error) {
		return []string{`\\?\usb#vid_04f2&pid_b6d9#...`}, nil
	}

	report, err := Diagnose()
	if err != nil {
		t.Fatalf("Diagnose() error = %v, want nil", err)
	}

	if !report.HasActiveCameras {
		t.Errorf("report.HasActiveCameras = false, want true")
	}
	if report.HasNoCamerasAttachedError {
		t.Errorf("report.HasNoCamerasAttachedError = true, want false")
	}
	if !strings.Contains(report.Summary, "healthy") {
		t.Errorf("report.Summary = %q, want containing 'healthy'", report.Summary)
	}
}

func TestDiagnose_PnPStatusOk_ZeroCaptureInterfaces(t *testing.T) {
	origCoInit := coInitializeEx
	origCoUninit := coUninitialize
	origMFStart := mfStartup
	origMFShut := mfShutdown
	origMFCreateAttr := mfCreateAttributes
	origMFEnum := mfEnumDeviceSources
	origCoFree := coTaskMemFree
	origCMGetIface := cmGetDeviceInterfaceList
	origSetupDiGetClassDevs := setupDiGetClassDevsEx
	origSetupDiEnum := setupDiEnumDeviceInfo
	origSetupDiGetProp := setupDiGetDeviceProperty
	origSetupDiGetRegProp := setupDiGetDeviceRegistryProperty
	origSetupDiGetInstID := setupDiGetDeviceInstanceID
	origCMGetStatus := cmGetDevNodeStatus

	t.Cleanup(func() {
		coInitializeEx = origCoInit
		coUninitialize = origCoUninit
		mfStartup = origMFStart
		mfShutdown = origMFShut
		mfCreateAttributes = origMFCreateAttr
		mfEnumDeviceSources = origMFEnum
		coTaskMemFree = origCoFree
		cmGetDeviceInterfaceList = origCMGetIface
		setupDiGetClassDevsEx = origSetupDiGetClassDevs
		setupDiEnumDeviceInfo = origSetupDiEnum
		setupDiGetDeviceProperty = origSetupDiGetProp
		setupDiGetDeviceRegistryProperty = origSetupDiGetRegProp
		setupDiGetDeviceInstanceID = origSetupDiGetInstID
		cmGetDevNodeStatus = origCMGetStatus
	})

	coInitializeEx = func(uintptr, uint32) error { return nil }
	coUninitialize = func() {}
	mfStartup = func(uint32, uint32) error { return nil }
	mfShutdown = func() error { return nil }
	coTaskMemFree = func(unsafe.Pointer) {}

	var attrVtbl [50]uintptr
	attrVtbl[2] = syscall.NewCallback(func(this uintptr) uintptr { return 1 })
	attrVtbl[24] = syscall.NewCallback(func(this, pKey, pVal uintptr) uintptr { return 0 })
	mockAttrCOM := &comObject{vtbl: &attrVtbl}

	mfCreateAttributes = func(ppMFAttributes **comObject, cInitialSize uint32) error {
		*ppMFAttributes = mockAttrCOM
		return nil
	}

	// Media Foundation finds 0 cameras (0xA00F4244).
	mfEnumDeviceSources = func(pAttributes *comObject, pppSourceActivate ***comObject, pcSourceActivate *uint32) int32 {
		*pcSourceActivate = 0
		*pppSourceActivate = nil
		return 0
	}

	// No active device interfaces.
	cmGetDeviceInterfaceList = func(deviceID string, ifaceClass *windows.GUID, flags uint32) ([]string, error) {
		return []string{}, nil
	}

	// Mock PnP returning healthy MIPI components (status OK, ProblemCode 0).
	mockPnPList := []struct {
		name       string
		instanceID string
	}{
		{name: "Intel(R) MTL AVStream Camera", instanceID: `ACPI\INTC1070\1`},
		{name: "Camera Sensor OV08X40", instanceID: `ACPI\OVTI08X4\1`},
		{name: "Intel(R) Control Logic", instanceID: `ACPI\INT3480\1`},
		{name: "Intel(R) Imaging Signal Processor", instanceID: `PCI\VEN_8086&DEV_7D19`},
	}

	setupDiGetClassDevsEx = func(classGUID *windows.GUID, enumerator string, hwndParent uintptr, flags windows.DIGCF, deviceInfoSet windows.DevInfo, machineName string) (windows.DevInfo, error) {
		if *classGUID == guidDevClassCamera {
			return windows.DevInfo(100), nil
		}
		return windows.DevInfo(windows.InvalidHandle), errors.New("no devices")
	}

	setupDiEnumDeviceInfo = func(deviceInfoSet windows.DevInfo, memberIndex int) (*windows.DevInfoData, error) {
		if memberIndex < len(mockPnPList) {
			return &windows.DevInfoData{
				DevInst: windows.DEVINST(memberIndex + 1),
			}, nil
		}
		return nil, windows.ERROR_NO_MORE_ITEMS
	}

	setupDiGetDeviceProperty = func(deviceInfoSet windows.DevInfo, deviceInfoData *windows.DevInfoData, propertyKey *windows.DEVPROPKEY) (any, error) {
		idx := int(deviceInfoData.DevInst) - 1
		if idx >= 0 && idx < len(mockPnPList) {
			if propertyKey.PID == devpkeyDeviceFriendlyName.PID {
				return mockPnPList[idx].name, nil
			}
		}
		return nil, errors.New("not found")
	}

	setupDiGetDeviceRegistryProperty = func(deviceInfoSet windows.DevInfo, deviceInfoData *windows.DevInfoData, property windows.SPDRP) (any, error) {
		idx := int(deviceInfoData.DevInst) - 1
		if idx >= 0 && idx < len(mockPnPList) {
			return mockPnPList[idx].name, nil
		}
		return nil, errors.New("not found")
	}

	setupDiGetDeviceInstanceID = func(deviceInfoSet windows.DevInfo, deviceInfoData *windows.DevInfoData) (string, error) {
		idx := int(deviceInfoData.DevInst) - 1
		if idx >= 0 && idx < len(mockPnPList) {
			return mockPnPList[idx].instanceID, nil
		}
		return "", errors.New("not found")
	}

	cmGetDevNodeStatus = func(status *uint32, problemNumber *uint32, devInst windows.DEVINST, flags uint32) error {
		*status = 0
		*problemNumber = 0 // Status OK!
		return nil
	}

	report, err := Diagnose()
	if err != nil {
		t.Fatalf("Diagnose() error = %v, want nil", err)
	}

	if report.HasActiveCameras {
		t.Errorf("report.HasActiveCameras = true, want false")
	}
	if !report.HasNoCamerasAttachedError {
		t.Errorf("report.HasNoCamerasAttachedError = false, want true")
	}
	if report.ErrorCode != ErrorStringNoCamerasAttached {
		t.Errorf("report.ErrorCode = %q, want %q", report.ErrorCode, ErrorStringNoCamerasAttached)
	}
	if !report.MIPISubsystem.HasSensor || !report.MIPISubsystem.HasAVStream {
		t.Errorf("report.MIPISubsystem sensor/avstream missing: %+v", report.MIPISubsystem)
	}
	if !strings.Contains(report.Summary, "0xA00F4244") ||
		!strings.Contains(report.Summary, "no active video capture interfaces") {
		t.Errorf("report.Summary = %q, want containing '0xA00F4244' and 'no active video capture interfaces'", report.Summary)
	}
}

func TestListCameras_GenericErrorDoesNotReturn0xA00F4244(t *testing.T) {
	origCoInit := coInitializeEx
	origCoUninit := coUninitialize
	origMFStart := mfStartup
	origMFShut := mfShutdown
	origMFCreateAttr := mfCreateAttributes
	origMFEnum := mfEnumDeviceSources
	origCoFree := coTaskMemFree
	t.Cleanup(func() {
		coInitializeEx = origCoInit
		coUninitialize = origCoUninit
		mfStartup = origMFStart
		mfShutdown = origMFShut
		mfCreateAttributes = origMFCreateAttr
		mfEnumDeviceSources = origMFEnum
		coTaskMemFree = origCoFree
	})

	coInitializeEx = func(uintptr, uint32) error { return nil }
	coUninitialize = func() {}
	mfStartup = func(uint32, uint32) error { return nil }
	mfShutdown = func() error { return nil }
	coTaskMemFree = func(unsafe.Pointer) {}

	var attrVtbl [50]uintptr
	attrVtbl[2] = syscall.NewCallback(func(this uintptr) uintptr { return 1 })
	attrVtbl[24] = syscall.NewCallback(func(this, pKey, pVal uintptr) uintptr { return 0 })
	mockAttrCOM := &comObject{vtbl: &attrVtbl}

	mfCreateAttributes = func(ppMFAttributes **comObject, cInitialSize uint32) error {
		*ppMFAttributes = mockAttrCOM
		return nil
	}

	// E_FAIL (0x80004005) - generic COM failure.
	mfEnumDeviceSources = func(pAttributes *comObject, pppSourceActivate ***comObject, pcSourceActivate *uint32) int32 {
		return -2147467259 // 0x80004005
	}

	_, err := ListCameras()
	if err == nil {
		t.Fatalf("ListCameras() error = nil, want error")
	}
	if IsNoCamerasAttachedError(err) {
		t.Errorf("IsNoCamerasAttachedError(%v) = true, want false for generic E_FAIL", err)
	}
}

func TestListCameras_MF_E_NO_CAPTURE_DEVICES_AVAILABLE(t *testing.T) {
	origCoInit := coInitializeEx
	origCoUninit := coUninitialize
	origMFStart := mfStartup
	origMFShut := mfShutdown
	origMFCreateAttr := mfCreateAttributes
	origMFEnum := mfEnumDeviceSources
	origCoFree := coTaskMemFree
	t.Cleanup(func() {
		coInitializeEx = origCoInit
		coUninitialize = origCoUninit
		mfStartup = origMFStart
		mfShutdown = origMFShut
		mfCreateAttributes = origMFCreateAttr
		mfEnumDeviceSources = origMFEnum
		coTaskMemFree = origCoFree
	})

	coInitializeEx = func(uintptr, uint32) error { return nil }
	coUninitialize = func() {}
	mfStartup = func(uint32, uint32) error { return nil }
	mfShutdown = func() error { return nil }
	coTaskMemFree = func(unsafe.Pointer) {}

	var attrVtbl [50]uintptr
	attrVtbl[2] = syscall.NewCallback(func(this uintptr) uintptr { return 1 })
	attrVtbl[24] = syscall.NewCallback(func(this, pKey, pVal uintptr) uintptr { return 0 })
	mockAttrCOM := &comObject{vtbl: &attrVtbl}

	mfCreateAttributes = func(ppMFAttributes **comObject, cInitialSize uint32) error {
		*ppMFAttributes = mockAttrCOM
		return nil
	}

	// MF_E_NO_CAPTURE_DEVICES_AVAILABLE (0xC00DABE0 = -1072845856).
	mfEnumDeviceSources = func(pAttributes *comObject, pppSourceActivate ***comObject, pcSourceActivate *uint32) int32 {
		return -1072845856
	}

	_, err := ListCameras()
	if !IsNoCamerasAttachedError(err) {
		t.Errorf("ListCameras() err = %v, want 0xA00F4244 for MF_E_NO_CAPTURE_DEVICES_AVAILABLE", err)
	}
}

func TestDiagnose_MIPIComponentError(t *testing.T) {
	origCoInit := coInitializeEx
	origCoUninit := coUninitialize
	origMFStart := mfStartup
	origMFShut := mfShutdown
	origMFCreateAttr := mfCreateAttributes
	origMFEnum := mfEnumDeviceSources
	origCoFree := coTaskMemFree
	origCMGetIface := cmGetDeviceInterfaceList
	origSetupDiGetClassDevs := setupDiGetClassDevsEx
	origSetupDiEnum := setupDiEnumDeviceInfo
	origSetupDiGetProp := setupDiGetDeviceProperty
	origSetupDiGetRegProp := setupDiGetDeviceRegistryProperty
	origSetupDiGetInstID := setupDiGetDeviceInstanceID
	origCMGetStatus := cmGetDevNodeStatus

	t.Cleanup(func() {
		coInitializeEx = origCoInit
		coUninitialize = origCoUninit
		mfStartup = origMFStart
		mfShutdown = origMFShut
		mfCreateAttributes = origMFCreateAttr
		mfEnumDeviceSources = origMFEnum
		coTaskMemFree = origCoFree
		cmGetDeviceInterfaceList = origCMGetIface
		setupDiGetClassDevsEx = origSetupDiGetClassDevs
		setupDiEnumDeviceInfo = origSetupDiEnum
		setupDiGetDeviceProperty = origSetupDiGetProp
		setupDiGetDeviceRegistryProperty = origSetupDiGetRegProp
		setupDiGetDeviceInstanceID = origSetupDiGetInstID
		cmGetDevNodeStatus = origCMGetStatus
	})

	coInitializeEx = func(uintptr, uint32) error { return nil }
	coUninitialize = func() {}
	mfStartup = func(uint32, uint32) error { return nil }
	mfShutdown = func() error { return nil }
	coTaskMemFree = func(unsafe.Pointer) {}

	var attrVtbl [50]uintptr
	attrVtbl[2] = syscall.NewCallback(func(this uintptr) uintptr { return 1 })
	attrVtbl[24] = syscall.NewCallback(func(this, pKey, pVal uintptr) uintptr { return 0 })
	mockAttrCOM := &comObject{vtbl: &attrVtbl}

	mfCreateAttributes = func(ppMFAttributes **comObject, cInitialSize uint32) error {
		*ppMFAttributes = mockAttrCOM
		return nil
	}

	mfEnumDeviceSources = func(pAttributes *comObject, pppSourceActivate ***comObject, pcSourceActivate *uint32) int32 {
		*pcSourceActivate = 0
		*pppSourceActivate = nil
		return 0
	}

	cmGetDeviceInterfaceList = func(deviceID string, ifaceClass *windows.GUID, flags uint32) ([]string, error) {
		return nil, errors.New("none")
	}

	mockPnPList := []struct {
		name        string
		instanceID  string
		problemCode uint32
	}{
		{
			name:        "Intel(R) MTL AVStream Camera",
			instanceID:  `ACPI\INTC1070\1`,
			problemCode: 10,
		},
	}

	setupDiGetClassDevsEx = func(classGUID *windows.GUID, enumerator string, hwndParent uintptr, flags windows.DIGCF, deviceInfoSet windows.DevInfo, machineName string) (windows.DevInfo, error) {
		if *classGUID == guidDevClassCamera {
			return windows.DevInfo(100), nil
		}
		return windows.DevInfo(windows.InvalidHandle), errors.New("no devices")
	}

	setupDiEnumDeviceInfo = func(deviceInfoSet windows.DevInfo, memberIndex int) (*windows.DevInfoData, error) {
		if memberIndex < len(mockPnPList) {
			return &windows.DevInfoData{
				DevInst: windows.DEVINST(memberIndex + 1),
			}, nil
		}
		return nil, windows.ERROR_NO_MORE_ITEMS
	}

	setupDiGetDeviceProperty = func(deviceInfoSet windows.DevInfo, deviceInfoData *windows.DevInfoData, propertyKey *windows.DEVPROPKEY) (any, error) {
		idx := int(deviceInfoData.DevInst) - 1
		if idx >= 0 && idx < len(mockPnPList) {
			if propertyKey.PID == devpkeyDeviceFriendlyName.PID {
				return mockPnPList[idx].name, nil
			}
		}
		return nil, errors.New("not found")
	}

	setupDiGetDeviceRegistryProperty = func(deviceInfoSet windows.DevInfo, deviceInfoData *windows.DevInfoData, property windows.SPDRP) (any, error) {
		idx := int(deviceInfoData.DevInst) - 1
		if idx >= 0 && idx < len(mockPnPList) {
			return mockPnPList[idx].name, nil
		}
		return nil, errors.New("not found")
	}

	setupDiGetDeviceInstanceID = func(deviceInfoSet windows.DevInfo, deviceInfoData *windows.DevInfoData) (string, error) {
		idx := int(deviceInfoData.DevInst) - 1
		if idx >= 0 && idx < len(mockPnPList) {
			return mockPnPList[idx].instanceID, nil
		}
		return "", errors.New("not found")
	}

	cmGetDevNodeStatus = func(status *uint32, problemNumber *uint32, devInst windows.DEVINST, flags uint32) error {
		*status = 0
		*problemNumber = 10 // Code 10: Failed Start
		return nil
	}

	report, err := Diagnose()
	if err != nil {
		t.Fatalf("Diagnose() error = %v, want nil", err)
	}

	if !report.HasNoCamerasAttachedError {
		t.Errorf("report.HasNoCamerasAttachedError = false, want true")
	}
	if !strings.Contains(report.Summary, "device errors") {
		t.Errorf("report.Summary = %q, want containing 'device errors'", report.Summary)
	}
}

func TestListActiveDeviceInterfaces(t *testing.T) {
	origCMGetIface := cmGetDeviceInterfaceList
	t.Cleanup(func() {
		cmGetDeviceInterfaceList = origCMGetIface
	})

	cmGetDeviceInterfaceList = func(deviceID string, ifaceClass *windows.GUID, flags uint32) ([]string, error) {
		if *ifaceClass == ksCategoryVideoCamera {
			return []string{`\\?\display#intc1070#...`}, nil
		}
		return nil, errors.New("none")
	}

	ifaces, err := ListActiveDeviceInterfaces()
	if err != nil {
		t.Fatalf("ListActiveDeviceInterfaces() error = %v, want nil", err)
	}
	if len(ifaces) != 1 {
		t.Fatalf("len(ifaces) = %d, want 1", len(ifaces))
	}
	if ifaces[0] != `\\?\display#intc1070#...` {
		t.Errorf("ifaces[0] = %q, want %q", ifaces[0], `\\?\display#intc1070#...`)
	}
}

func TestListPnPDevices(t *testing.T) {
	origSetupDiGetClassDevs := setupDiGetClassDevsEx
	origSetupDiEnum := setupDiEnumDeviceInfo
	origSetupDiGetProp := setupDiGetDeviceProperty
	origSetupDiGetRegProp := setupDiGetDeviceRegistryProperty
	origSetupDiGetInstID := setupDiGetDeviceInstanceID
	origCMGetStatus := cmGetDevNodeStatus

	t.Cleanup(func() {
		setupDiGetClassDevsEx = origSetupDiGetClassDevs
		setupDiEnumDeviceInfo = origSetupDiEnum
		setupDiGetDeviceProperty = origSetupDiGetProp
		setupDiGetDeviceRegistryProperty = origSetupDiGetRegProp
		setupDiGetDeviceInstanceID = origSetupDiGetInstID
		cmGetDevNodeStatus = origCMGetStatus
	})

	setupDiGetClassDevsEx = func(classGUID *windows.GUID, enumerator string, hwndParent uintptr, flags windows.DIGCF, deviceInfoSet windows.DevInfo, machineName string) (windows.DevInfo, error) {
		if *classGUID == guidDevClassCamera {
			return windows.DevInfo(100), nil
		}
		return windows.DevInfo(windows.InvalidHandle), errors.New("no devices")
	}

	setupDiEnumDeviceInfo = func(deviceInfoSet windows.DevInfo, memberIndex int) (*windows.DevInfoData, error) {
		if memberIndex == 0 {
			return &windows.DevInfoData{DevInst: windows.DEVINST(1)}, nil
		}
		return nil, windows.ERROR_NO_MORE_ITEMS
	}

	setupDiGetDeviceProperty = func(deviceInfoSet windows.DevInfo, deviceInfoData *windows.DevInfoData, propertyKey *windows.DEVPROPKEY) (any, error) {
		if propertyKey.PID == devpkeyDeviceFriendlyName.PID {
			return "Intel(R) MTL AVStream Camera", nil
		}
		if propertyKey.PID == devpkeyDeviceDriverInfPath.PID {
			return `C:\Windows\System32\DriverStore\FileRepository\iacamera64.inf_amd64_12345\iacamera64.inf`, nil
		}
		if propertyKey.PID == devpkeyDeviceDriverVersion.PID {
			return "70.26100.2.18597", nil
		}
		return nil, errors.New("not found")
	}

	setupDiGetDeviceRegistryProperty = func(deviceInfoSet windows.DevInfo, deviceInfoData *windows.DevInfoData, property windows.SPDRP) (any, error) {
		return "Intel(R) MTL AVStream Camera", nil
	}

	setupDiGetDeviceInstanceID = func(deviceInfoSet windows.DevInfo, deviceInfoData *windows.DevInfoData) (string, error) {
		return `ACPI\INTC1070\1`, nil
	}

	cmGetDevNodeStatus = func(status *uint32, problemNumber *uint32, devInst windows.DEVINST, flags uint32) error {
		*status = 0
		*problemNumber = 0
		return nil
	}

	devs, err := ListPnPDevices()
	if err != nil {
		t.Fatalf("ListPnPDevices() error = %v, want nil", err)
	}
	if len(devs) != 1 {
		t.Fatalf("len(devs) = %d, want 1", len(devs))
	}
	dev := devs[0]
	if dev.FriendlyName != "Intel(R) MTL AVStream Camera" {
		t.Errorf("dev.FriendlyName = %q, want %q", dev.FriendlyName, "Intel(R) MTL AVStream Camera")
	}
	if dev.DriverInfPath != "iacamera64.inf" {
		t.Errorf("dev.DriverInfPath = %q, want %q", dev.DriverInfPath, "iacamera64.inf")
	}
	if dev.DriverVersion != "70.26100.2.18597" {
		t.Errorf("dev.DriverVersion = %q, want %q", dev.DriverVersion, "70.26100.2.18597")
	}
	if dev.ProblemCode != 0 {
		t.Errorf("dev.ProblemCode = %d, want 0", dev.ProblemCode)
	}
}

func TestDiagnose_ListCamerasGenericErrorReturnsError(t *testing.T) {
	origCoInit := coInitializeEx
	origCoUninit := coUninitialize
	origMFStart := mfStartup
	origMFShut := mfShutdown
	origMFCreateAttr := mfCreateAttributes
	origMFEnum := mfEnumDeviceSources
	origCoFree := coTaskMemFree

	t.Cleanup(func() {
		coInitializeEx = origCoInit
		coUninitialize = origCoUninit
		mfStartup = origMFStart
		mfShutdown = origMFShut
		mfCreateAttributes = origMFCreateAttr
		mfEnumDeviceSources = origMFEnum
		coTaskMemFree = origCoFree
	})

	coInitializeEx = func(uintptr, uint32) error { return nil }
	coUninitialize = func() {}
	mfStartup = func(uint32, uint32) error { return errors.New("MFStartup fatal failure") }
	mfShutdown = func() error { return nil }
	coTaskMemFree = func(unsafe.Pointer) {}

	report, err := Diagnose()
	if err == nil {
		t.Fatalf("Diagnose() error = nil, want error for MFStartup failure")
	}
	if report != nil {
		t.Errorf("Diagnose() report = %v, want nil on fatal error", report)
	}
	if !strings.Contains(err.Error(), "MFStartup fatal failure") {
		t.Errorf("Diagnose() error = %v, want MFStartup error", err)
	}
}

func TestGetDeviceFriendlyName(t *testing.T) {
	origSetupDiGetDeviceRegistryProperty := setupDiGetDeviceRegistryProperty
	origSetupDiGetDeviceProperty := setupDiGetDeviceProperty
	t.Cleanup(func() {
		setupDiGetDeviceRegistryProperty = origSetupDiGetDeviceRegistryProperty
		setupDiGetDeviceProperty = origSetupDiGetDeviceProperty
	})

	t.Run("from devpkey friendly name", func(t *testing.T) {
		setupDiGetDeviceProperty = func(deviceInfoSet windows.DevInfo, deviceInfoData *windows.DevInfoData, propertyKey *windows.DEVPROPKEY) (any, error) {
			if *propertyKey == devpkeyDeviceFriendlyName {
				return "Intel(R) MTL AVStream Camera", nil
			}
			return nil, errors.New("not found")
		}
		setupDiGetDeviceRegistryProperty = func(deviceInfoSet windows.DevInfo, deviceInfoData *windows.DevInfoData, property windows.SPDRP) (any, error) {
			return nil, errors.New("not found")
		}

		got := GetDeviceFriendlyName(windows.DevInfo(1), &windows.DevInfoData{})
		if got != "Intel(R) MTL AVStream Camera" {
			t.Errorf("GetDeviceFriendlyName() = %q, want 'Intel(R) MTL AVStream Camera'", got)
		}
	})

	t.Run("from registry friendly name", func(t *testing.T) {
		setupDiGetDeviceProperty = func(deviceInfoSet windows.DevInfo, deviceInfoData *windows.DevInfoData, propertyKey *windows.DEVPROPKEY) (any, error) {
			return nil, errors.New("not found")
		}
		setupDiGetDeviceRegistryProperty = func(deviceInfoSet windows.DevInfo, deviceInfoData *windows.DevInfoData, property windows.SPDRP) (any, error) {
			if property == windows.SPDRP_FRIENDLYNAME {
				return "Integrated Camera", nil
			}
			return nil, errors.New("not found")
		}

		got := GetDeviceFriendlyName(windows.DevInfo(1), &windows.DevInfoData{})
		if got != "Integrated Camera" {
			t.Errorf("GetDeviceFriendlyName() = %q, want 'Integrated Camera'", got)
		}
	})

	t.Run("from devpkey device desc", func(t *testing.T) {
		setupDiGetDeviceProperty = func(deviceInfoSet windows.DevInfo, deviceInfoData *windows.DevInfoData, propertyKey *windows.DEVPROPKEY) (any, error) {
			if *propertyKey == devpkeyDeviceDeviceDesc {
				return "Intel(R) Control Logic", nil
			}
			return nil, errors.New("not found")
		}
		setupDiGetDeviceRegistryProperty = func(deviceInfoSet windows.DevInfo, deviceInfoData *windows.DevInfoData, property windows.SPDRP) (any, error) {
			return nil, errors.New("not found")
		}

		got := GetDeviceFriendlyName(windows.DevInfo(1), &windows.DevInfoData{})
		if got != "Intel(R) Control Logic" {
			t.Errorf("GetDeviceFriendlyName() = %q, want 'Intel(R) Control Logic'", got)
		}
	})

	t.Run("from registry device desc", func(t *testing.T) {
		setupDiGetDeviceProperty = func(deviceInfoSet windows.DevInfo, deviceInfoData *windows.DevInfoData, propertyKey *windows.DEVPROPKEY) (any, error) {
			return nil, errors.New("not found")
		}
		setupDiGetDeviceRegistryProperty = func(deviceInfoSet windows.DevInfo, deviceInfoData *windows.DevInfoData, property windows.SPDRP) (any, error) {
			if property == windows.SPDRP_DEVICEDESC {
				return "Camera Sensor OV08X40", nil
			}
			return nil, errors.New("not found")
		}

		got := GetDeviceFriendlyName(windows.DevInfo(1), &windows.DevInfoData{})
		if got != "Camera Sensor OV08X40" {
			t.Errorf("GetDeviceFriendlyName() = %q, want 'Camera Sensor OV08X40'", got)
		}
	})

	t.Run("not found returns empty", func(t *testing.T) {
		setupDiGetDeviceProperty = func(deviceInfoSet windows.DevInfo, deviceInfoData *windows.DevInfoData, propertyKey *windows.DEVPROPKEY) (any, error) {
			return nil, errors.New("not found")
		}
		setupDiGetDeviceRegistryProperty = func(deviceInfoSet windows.DevInfo, deviceInfoData *windows.DevInfoData, property windows.SPDRP) (any, error) {
			return nil, errors.New("not found")
		}

		got := GetDeviceFriendlyName(windows.DevInfo(1), &windows.DevInfoData{})
		if got != "" {
			t.Errorf("GetDeviceFriendlyName() = %q, want empty", got)
		}
	})
}

func TestGetDeviceDriverInfPath(t *testing.T) {
	origSetupDiGetDeviceProperty := setupDiGetDeviceProperty
	t.Cleanup(func() {
		setupDiGetDeviceProperty = origSetupDiGetDeviceProperty
	})

	setupDiGetDeviceProperty = func(deviceInfoSet windows.DevInfo, deviceInfoData *windows.DevInfoData, propertyKey *windows.DEVPROPKEY) (any, error) {
		if *propertyKey == devpkeyDeviceDriverInfPath {
			return `C:\Windows\INF\oem42.inf`, nil
		}
		return nil, errors.New("not found")
	}

	got, err := GetDeviceDriverInfPath(windows.DevInfo(1), &windows.DevInfoData{})
	if err != nil {
		t.Fatalf("GetDeviceDriverInfPath() error = %v, want nil", err)
	}
	if got != "oem42.inf" {
		t.Errorf("GetDeviceDriverInfPath() = %q, want 'oem42.inf'", got)
	}
}

func TestGetDeviceDriverVersion(t *testing.T) {
	origSetupDiGetDeviceProperty := setupDiGetDeviceProperty
	t.Cleanup(func() {
		setupDiGetDeviceProperty = origSetupDiGetDeviceProperty
	})

	setupDiGetDeviceProperty = func(deviceInfoSet windows.DevInfo, deviceInfoData *windows.DevInfoData, propertyKey *windows.DEVPROPKEY) (any, error) {
		if *propertyKey == devpkeyDeviceDriverVersion {
			return "1.2.3.4", nil
		}
		return nil, errors.New("not found")
	}

	got, err := GetDeviceDriverVersion(windows.DevInfo(1), &windows.DevInfoData{})
	if err != nil {
		t.Fatalf("GetDeviceDriverVersion() error = %v, want nil", err)
	}
	if got != "1.2.3.4" {
		t.Errorf("GetDeviceDriverVersion() = %q, want '1.2.3.4'", got)
	}
}

func TestGetDeviceNames(t *testing.T) {
	origSetupDiGetDeviceRegistryProperty := setupDiGetDeviceRegistryProperty
	origSetupDiGetDeviceProperty := setupDiGetDeviceProperty
	t.Cleanup(func() {
		setupDiGetDeviceRegistryProperty = origSetupDiGetDeviceRegistryProperty
		setupDiGetDeviceProperty = origSetupDiGetDeviceProperty
	})

	t.Run("from devpkey device desc", func(t *testing.T) {
		setupDiGetDeviceProperty = func(deviceInfoSet windows.DevInfo, deviceInfoData *windows.DevInfoData, propertyKey *windows.DEVPROPKEY) (any, error) {
			if *propertyKey == devpkeyDeviceFriendlyName {
				return "Integrated Camera", nil
			}
			if *propertyKey == devpkeyDeviceDeviceDesc {
				return "Camera Sensor OV08X40", nil
			}
			return nil, errors.New("not found")
		}
		setupDiGetDeviceRegistryProperty = func(deviceInfoSet windows.DevInfo, deviceInfoData *windows.DevInfoData, property windows.SPDRP) (any, error) {
			return nil, errors.New("not found")
		}

		friendly, desc := getDeviceNames(windows.DevInfo(1), &windows.DevInfoData{})
		if friendly != "Integrated Camera" || desc != "Camera Sensor OV08X40" {
			t.Errorf("getDeviceNames() = (%q, %q), want ('Integrated Camera', 'Camera Sensor OV08X40')", friendly, desc)
		}
	})

	t.Run("from registry device desc when property errors", func(t *testing.T) {
		setupDiGetDeviceProperty = func(deviceInfoSet windows.DevInfo, deviceInfoData *windows.DevInfoData, propertyKey *windows.DEVPROPKEY) (any, error) {
			if *propertyKey == devpkeyDeviceFriendlyName {
				return "Integrated Camera", nil
			}
			return nil, errors.New("property error")
		}
		setupDiGetDeviceRegistryProperty = func(deviceInfoSet windows.DevInfo, deviceInfoData *windows.DevInfoData, property windows.SPDRP) (any, error) {
			if property == windows.SPDRP_DEVICEDESC {
				return "Camera Sensor OV08X40", nil
			}
			return nil, errors.New("not found")
		}

		friendly, desc := getDeviceNames(windows.DevInfo(1), &windows.DevInfoData{})
		if friendly != "Integrated Camera" || desc != "Camera Sensor OV08X40" {
			t.Errorf("getDeviceNames() = (%q, %q), want ('Integrated Camera', 'Camera Sensor OV08X40')", friendly, desc)
		}
	})

	t.Run("fallback to friendly name when both error", func(t *testing.T) {
		setupDiGetDeviceProperty = func(deviceInfoSet windows.DevInfo, deviceInfoData *windows.DevInfoData, propertyKey *windows.DEVPROPKEY) (any, error) {
			if *propertyKey == devpkeyDeviceFriendlyName {
				return "Integrated Camera", nil
			}
			return nil, errors.New("property error")
		}
		setupDiGetDeviceRegistryProperty = func(deviceInfoSet windows.DevInfo, deviceInfoData *windows.DevInfoData, property windows.SPDRP) (any, error) {
			return nil, errors.New("registry error")
		}

		friendly, desc := getDeviceNames(windows.DevInfo(1), &windows.DevInfoData{})
		if friendly != "Integrated Camera" || desc != "Integrated Camera" {
			t.Errorf("getDeviceNames() = (%q, %q), want ('Integrated Camera', 'Integrated Camera')", friendly, desc)
		}
	})
}
