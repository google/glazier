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
	"fmt"
	"path/filepath"
	"runtime"
	"strings"
	"syscall"
	"unsafe"

	"github.com/google/deck"
	"golang.org/x/sys/windows"
)

var (
	mfplatDLL = windows.NewLazySystemDLL("mfplat.dll")
	mfDLL     = windows.NewLazySystemDLL("mf.dll")
	ole32DLL  = windows.NewLazySystemDLL("ole32.dll")

	procMFStartup           = mfplatDLL.NewProc("MFStartup")
	procMFShutdown          = mfplatDLL.NewProc("MFShutdown")
	procMFCreateAttributes  = mfplatDLL.NewProc("MFCreateAttributes")
	procMFEnumDeviceSources = mfDLL.NewProc("MFEnumDeviceSources")
	procCoInitializeEx      = ole32DLL.NewProc("CoInitializeEx")
	procCoUninitialize      = ole32DLL.NewProc("CoUninitialize")
	procCoTaskMemFree       = ole32DLL.NewProc("CoTaskMemFree")

	// Media Foundation Attribute GUIDs
	guidMFDevSourceAttributeSourceType = windows.GUID{
		Data1: 0xc60ac5fe, Data2: 0x252a, Data3: 0x478f,
		Data4: [8]byte{0xa0, 0xef, 0xbc, 0x8f, 0xa5, 0xf7, 0xca, 0xd3},
	}
	guidMFDevSourceAttributeSourceTypeVidCap = windows.GUID{
		Data1: 0x8ac3587a, Data2: 0x4ae7, Data3: 0x42d8,
		Data4: [8]byte{0x99, 0xe0, 0x0a, 0x60, 0x13, 0xee, 0xf9, 0x0f},
	}
	guidMFDevSourceAttributeFriendlyName = windows.GUID{
		Data1: 0x60d0e559, Data2: 0x52f8, Data3: 0x4fa2,
		Data4: [8]byte{0xbb, 0xce, 0xac, 0xdb, 0x34, 0xa8, 0xec, 0x01},
	}
	guidMFDevSourceAttributeVidCapSymbolicLink = windows.GUID{
		Data1: 0x58f0aad8, Data2: 0x22bf, Data3: 0x4f8a,
		Data4: [8]byte{0xbb, 0x3d, 0xd2, 0xc4, 0x97, 0x8c, 0x6e, 0x2f},
	}
	guidMFDevSourceAttributeVidCapCategory = windows.GUID{
		Data1: 0x77f0ae69, Data2: 0xc3bd, Data3: 0x4509,
		Data4: [8]byte{0x94, 0x1d, 0x46, 0x7e, 0x4d, 0x24, 0x89, 0x9e},
	}
	guidMFDevSourceAttributeVidCapHWSource = windows.GUID{
		Data1: 0xde7046ba, Data2: 0x54d6, Data3: 0x4487,
		Data4: [8]byte{0xa2, 0xa4, 0xec, 0x7c, 0x0d, 0x1b, 0xd1, 0x63},
	}

	// Device Interface Categories
	ksCategoryVideoCamera = windows.GUID{
		Data1: 0xE5323777, Data2: 0xF976, Data3: 0x464B,
		Data4: [8]byte{0x9B, 0x55, 0xB9, 0x46, 0x97, 0xC4, 0x9E, 0x44},
	}
	ksCategoryCapture = windows.GUID{
		Data1: 0x65E8773D, Data2: 0x8F56, Data3: 0x11D0,
		Data4: [8]byte{0xA3, 0xB9, 0x00, 0xA0, 0xC9, 0x22, 0x31, 0x96},
	}
	guidDevInterfaceCamera = windows.GUID{
		Data1: 0x24E552D7, Data2: 0x6523, Data3: 0x47F7,
		Data4: [8]byte{0xA6, 0x47, 0xD3, 0x46, 0x5B, 0xF1, 0xF5, 0xCA},
	}
	guidDevInterfaceImage = windows.GUID{
		Data1: 0x6BDD1FC6, Data2: 0x810F, Data3: 0x11D0,
		Data4: [8]byte{0xBE, 0xC7, 0x08, 0x00, 0x2B, 0xE2, 0x09, 0x2F},
	}

	// Device Setup Classes
	guidDevClassCamera = windows.GUID{
		Data1: 0x4D36E96C, Data2: 0xE325, Data3: 0x11CE,
		Data4: [8]byte{0xBF, 0xC1, 0x08, 0x00, 0x2B, 0xE1, 0x03, 0x18},
	}
	guidDevClassImage = windows.GUID{
		Data1: 0x6BDD1FC6, Data2: 0x810F, Data3: 0x11D0,
		Data4: [8]byte{0xBE, 0xC7, 0x08, 0x00, 0x2B, 0xE2, 0x09, 0x2F},
	}
	guidDevClassSystem = windows.GUID{
		Data1: 0x4D36E97D, Data2: 0xE325, Data3: 0x11CE,
		Data4: [8]byte{0xBF, 0xC1, 0x08, 0x00, 0x2B, 0xE1, 0x03, 0x18},
	}
	guidDevClassSensor = windows.GUID{
		Data1: 0x5175D334, Data2: 0xC371, Data3: 0x4806,
		Data4: [8]byte{0xB3, 0xBA, 0x71, 0xFD, 0x53, 0xC9, 0x25, 0x8D},
	}

	// PnP Property Keys
	devpkeyDeviceDriverVersion = windows.DEVPROPKEY{
		FmtID: windows.DEVPROPGUID{
			Data1: 0xa8b865dd, Data2: 0x2e3d, Data3: 0x4094,
			Data4: [8]byte{0xad, 0x97, 0xe5, 0x93, 0xa7, 0x0c, 0x75, 0xd6},
		},
		PID: 3,
	}
	devpkeyDeviceDriverInfPath = windows.DEVPROPKEY{
		FmtID: windows.DEVPROPGUID{
			Data1: 0xa8b865dd, Data2: 0x2e3d, Data3: 0x4094,
			Data4: [8]byte{0xad, 0x97, 0xe5, 0x93, 0xa7, 0x0c, 0x75, 0xd6},
		},
		PID: 5,
	}
	devpkeyDeviceFriendlyName = windows.DEVPROPKEY{
		FmtID: windows.DEVPROPGUID{
			Data1: 0xa45c254e, Data2: 0xdf1c, Data3: 0x4efd,
			Data4: [8]byte{0x80, 0x20, 0x67, 0xd1, 0x46, 0xa8, 0x50, 0xe0},
		},
		PID: 14,
	}
	devpkeyDeviceDeviceDesc = windows.DEVPROPKEY{
		FmtID: windows.DEVPROPGUID{
			Data1: 0xa45c254e, Data2: 0xdf1c, Data3: 0x4efd,
			Data4: [8]byte{0x80, 0x20, 0x67, 0xd1, 0x46, 0xa8, 0x50, 0xe0},
		},
		PID: 2,
	}

	// Test hooks and default implementations
	coInitializeEx               = defaultCoInitializeEx
	coUninitialize               = defaultCoUninitialize
	mfStartup                    = defaultMFStartup
	mfShutdown                   = defaultMFShutdown
	mfCreateAttributes           = defaultMFCreateAttributes
	mfEnumDeviceSources          = defaultMFEnumDeviceSources
	coTaskMemFree                = defaultCoTaskMemFree
	cmGetDeviceInterfaceList     = windows.CM_Get_Device_Interface_List
	cmGetDevNodeStatus           = windows.CM_Get_DevNode_Status
	setupDiGetClassDevsEx        = windows.SetupDiGetClassDevsEx
	setupDiDestroyDeviceInfoList = func(d windows.DevInfo) error { return d.Close() }
	setupDiEnumDeviceInfo        = windows.SetupDiEnumDeviceInfo
	setupDiGetDeviceProperty     = windows.SetupDiGetDeviceProperty
	setupDiGetDeviceRegistryProperty = windows.SetupDiGetDeviceRegistryProperty
	setupDiGetDeviceInstanceID   = windows.SetupDiGetDeviceInstanceId
)

func defaultCoInitializeEx(pvReserved uintptr, dwCoInit uint32) error {
	r1, _, _ := procCoInitializeEx.Call(pvReserved, uintptr(dwCoInit))
	if int32(r1) < 0 {
		return fmt.Errorf("CoInitializeEx failed: 0x%08X", uint32(r1))
	}
	return nil
}

func defaultCoUninitialize() {
	procCoUninitialize.Call()
}

func defaultMFStartup(version uint32, flags uint32) error {
	r1, _, _ := procMFStartup.Call(uintptr(version), uintptr(flags))
	if int32(r1) < 0 {
		return fmt.Errorf("MFStartup failed: 0x%08X", uint32(r1))
	}
	return nil
}

func defaultMFShutdown() error {
	r1, _, _ := procMFShutdown.Call()
	if int32(r1) < 0 {
		return fmt.Errorf("MFShutdown failed: 0x%08X", uint32(r1))
	}
	return nil
}

type comObject struct {
	vtbl *[50]uintptr
}

func defaultMFCreateAttributes(ppMFAttributes **comObject, cInitialSize uint32) error {
	r1, _, _ := procMFCreateAttributes.Call(uintptr(unsafe.Pointer(ppMFAttributes)), uintptr(cInitialSize))
	if int32(r1) < 0 {
		return fmt.Errorf("MFCreateAttributes failed: 0x%08X", uint32(r1))
	}
	return nil
}

func defaultMFEnumDeviceSources(pAttributes *comObject, pppSourceActivate ***comObject, pcSourceActivate *uint32) int32 {
	r1, _, _ := procMFEnumDeviceSources.Call(
		uintptr(unsafe.Pointer(pAttributes)),
		uintptr(unsafe.Pointer(pppSourceActivate)),
		uintptr(unsafe.Pointer(pcSourceActivate)),
	)
	return int32(r1)
}

func defaultCoTaskMemFree(pv unsafe.Pointer) {
	if pv != nil {
		procCoTaskMemFree.Call(uintptr(pv))
	}
}

// COM Helpers

func (c *comObject) release() {
	if c == nil || c.vtbl == nil {
		return
	}
	syscall.SyscallN(c.vtbl[2], uintptr(unsafe.Pointer(c))) // Release is Index 2
}

func (c *comObject) setGUID(key *windows.GUID, val *windows.GUID) error {
	if c == nil || c.vtbl == nil {
		return errors.New("nil COM interface pointer")
	}
	r1, _, _ := syscall.SyscallN(c.vtbl[24], uintptr(unsafe.Pointer(c)), uintptr(unsafe.Pointer(key)), uintptr(unsafe.Pointer(val))) // SetGUID is Index 24
	if int32(r1) < 0 {
		return fmt.Errorf("IMFAttributes::SetGUID failed: 0x%08X", uint32(r1))
	}
	return nil
}

func (c *comObject) getAllocatedString(key *windows.GUID) (string, error) {
	if c == nil || c.vtbl == nil {
		return "", errors.New("nil COM interface pointer")
	}
	var strPtr *uint16
	var cch uint32
	// GetAllocatedString is Index 13
	r1, _, _ := syscall.SyscallN(c.vtbl[13], uintptr(unsafe.Pointer(c)), uintptr(unsafe.Pointer(key)), uintptr(unsafe.Pointer(&strPtr)), uintptr(unsafe.Pointer(&cch)))
	if int32(r1) < 0 || strPtr == nil {
		return "", fmt.Errorf("IMFAttributes::GetAllocatedString failed: 0x%08X", uint32(r1))
	}
	defer coTaskMemFree(unsafe.Pointer(strPtr))
	return windows.UTF16PtrToString(strPtr), nil
}

func (c *comObject) getUINT32(key *windows.GUID) (uint32, error) {
	if c == nil || c.vtbl == nil {
		return 0, errors.New("nil COM interface pointer")
	}
	var val uint32
	// GetUINT32 is Index 7
	r1, _, _ := syscall.SyscallN(c.vtbl[7], uintptr(unsafe.Pointer(c)), uintptr(unsafe.Pointer(key)), uintptr(unsafe.Pointer(&val)))
	if int32(r1) < 0 {
		return 0, fmt.Errorf("IMFAttributes::GetUINT32 failed: 0x%08X", uint32(r1))
	}
	return val, nil
}

func (c *comObject) getGUID(key *windows.GUID) (windows.GUID, error) {
	if c == nil || c.vtbl == nil {
		return windows.GUID{}, errors.New("nil COM interface pointer")
	}
	var val windows.GUID
	// GetGUID is Index 10
	r1, _, _ := syscall.SyscallN(c.vtbl[10], uintptr(unsafe.Pointer(c)), uintptr(unsafe.Pointer(key)), uintptr(unsafe.Pointer(&val)))
	if int32(r1) < 0 {
		return windows.GUID{}, fmt.Errorf("IMFAttributes::GetGUID failed: 0x%08X", uint32(r1))
	}
	return val, nil
}

// ListCameras enumerates all active video capture devices via Windows Media Foundation
// without opening video streams or illuminating privacy indicator LEDs.
//
// If 0 capture devices are found, or if Media Foundation returns a capture device error,
// it returns ErrNoCamerasAttached (error code 0xA00F4244).
func ListCameras() ([]CameraInfo, error) {
	runtime.LockOSThread()
	defer runtime.UnlockOSThread()

	deck.Infof("Initializing Media Foundation to enumerate active video capture sources...")

	// Initialize COM for this thread.
	if err := coInitializeEx(0, windows.COINIT_MULTITHREADED); err == nil {
		defer coUninitialize()
	}

	const mfVersion = 0x00020070
	const mfStartupNoSocket = 1
	if err := mfStartup(mfVersion, mfStartupNoSocket); err != nil {
		return nil, fmt.Errorf("MFStartup failed: %w", err)
	}
	defer mfShutdown()

	var pAttributes *comObject
	if err := mfCreateAttributes(&pAttributes, 1); err != nil {
		return nil, fmt.Errorf("MFCreateAttributes failed: %w", err)
	}
	defer pAttributes.release()

	if err := pAttributes.setGUID(&guidMFDevSourceAttributeSourceType, &guidMFDevSourceAttributeSourceTypeVidCap); err != nil {
		return nil, fmt.Errorf("setting vidcap attribute: %w", err)
	}

	var devicesPtr **comObject
	var count uint32
	hr := mfEnumDeviceSources(pAttributes, &devicesPtr, &count)
	if hr != 0 {
		uhr := uint32(hr)
		deck.Warningf("MFEnumDeviceSources returned error HRESULT: 0x%08X", uhr)
		if uhr == ErrorCodeNoCamerasAttached || hr == HResultNoCamerasAttached || uhr == 0xC00DABE0 || uhr == 0x80070490 || uhr == 0xC00D36D5 {
			return nil, ErrNoCamerasAttached
		}
		return nil, fmt.Errorf("MFEnumDeviceSources failed with HRESULT 0x%08X", uhr)
	}

	deck.Infof("Media Foundation reported %d video capture device source(s)", count)

	if count == 0 {
		if devicesPtr != nil {
			coTaskMemFree(unsafe.Pointer(devicesPtr))
		}
		deck.Infof("No active capture sources found -> error 0xA00F4244 <NoCamerasAreAttached>")
		return nil, ErrNoCamerasAttached
	}

	defer coTaskMemFree(unsafe.Pointer(devicesPtr))

	activates := unsafe.Slice(devicesPtr, count)
	var cameras []CameraInfo
	for i := uint32(0); i < count; i++ {
		pActivate := activates[i]
		if pActivate == nil {
			continue
		}

		friendlyName, _ := pActivate.getAllocatedString(&guidMFDevSourceAttributeFriendlyName)
		symLink, _ := pActivate.getAllocatedString(&guidMFDevSourceAttributeVidCapSymbolicLink)
		catGUID, _ := pActivate.getGUID(&guidMFDevSourceAttributeVidCapCategory)
		hwSource, _ := pActivate.getUINT32(&guidMFDevSourceAttributeVidCapHWSource)

		// Safely release IMFActivate without calling ActivateObject (prevents hardware LED flash).
		pActivate.release()

		displayName := friendlyName
		if displayName == "" {
			displayName = symLink
		}

		isMIPI := IsMIPICamera(friendlyName, symLink)
		deck.Infof("Found Media Foundation camera [%d/%d]: Name=%q, SymbolicLink=%q, IsMIPI=%v, Hardware=%v, Category=%s",
			i+1, count, displayName, symLink, isMIPI, hwSource != 0, catGUID.String())

		cameras = append(cameras, CameraInfo{
			Name:           displayName,
			SymbolicLink:   symLink,
			Category:       catGUID.String(),
			HardwareSource: hwSource != 0,
			IsMIPI:         isMIPI,
		})
	}

	if len(cameras) == 0 {
		return nil, ErrNoCamerasAttached
	}

	return cameras, nil
}

// ListActiveDeviceInterfaces enumerates currently active PnP device interface paths
// registered under ksCategoryVideoCamera, ksCategoryCapture, guidDevInterfaceCamera,
// and guidDevInterfaceImage.
func ListActiveDeviceInterfaces() ([]string, error) {
	guids := []*windows.GUID{
		&ksCategoryVideoCamera,
		&ksCategoryCapture,
		&guidDevInterfaceCamera,
		&guidDevInterfaceImage,
	}

	deck.Infof("Querying PnP device interfaces (ksCategoryVideoCamera, ksCategoryCapture, guidDevInterfaceCamera)...")

	seen := make(map[string]bool)
	var results []string

	for _, g := range guids {
		list, err := cmGetDeviceInterfaceList("", g, windows.CM_GET_DEVICE_INTERFACE_LIST_PRESENT)
		if err != nil {
			continue
		}
		for _, iface := range list {
			lower := strings.ToLower(iface)
			if iface != "" && !seen[lower] {
				seen[lower] = true
				deck.Infof("Found active device interface: %s", iface)
				results = append(results, iface)
			}
		}
	}

	deck.Infof("Total active device interfaces found: %d", len(results))
	return results, nil
}

// ListPnPDevices queries the Windows PnP tree for Camera, Image, System, and Sensor devices,
// retrieving their status, problem codes, driver INF names, and hardware IDs.
func ListPnPDevices() ([]PnPDevice, error) {
	classes := []*windows.GUID{
		&guidDevClassCamera,
		&guidDevClassImage,
		&guidDevClassSystem,
		&guidDevClassSensor,
	}

	deck.Infof("Scanning PnP device tree for Camera, Image, System, and Sensor classes...")

	var devices []PnPDevice
	seen := make(map[string]bool)

	for _, classGUID := range classes {
		devInfo, err := setupDiGetClassDevsEx(classGUID, "", 0, windows.DIGCF_PRESENT, 0, "")
		if err != nil {
			continue
		}
		func() {
			defer setupDiDestroyDeviceInfoList(devInfo)
			for i := 0; ; i++ {
				devInfoData, err := setupDiEnumDeviceInfo(devInfo, i)
				if err != nil {
					break
				}
				friendlyName, deviceDesc := getDeviceNames(devInfo, devInfoData)
				instanceID, err := setupDiGetDeviceInstanceID(devInfo, devInfoData)
				if err != nil || instanceID == "" {
					continue
				}
				key := strings.ToLower(instanceID)
				if seen[key] {
					continue
				}

				infPath, _ := getDeviceDriverInfPath(devInfo, devInfoData)
				version, _ := getDeviceDriverVersion(devInfo, devInfoData)

				if !isRelevantPnPDevice(friendlyName, deviceDesc, instanceID, infPath, classGUID) {
					continue
				}
				seen[key] = true

				var status, problemCode uint32
				_ = cmGetDevNodeStatus(&status, &problemCode, devInfoData.DevInst, 0)

				className := "Unknown"
				switch *classGUID {
				case guidDevClassCamera:
					className = "Camera"
				case guidDevClassImage:
					className = "Image"
				case guidDevClassSystem:
					className = "System"
				case guidDevClassSensor:
					className = "Sensor"
				}

				probDesc := ProblemCodeDescription(problemCode)
				deck.Infof("Found PnP Device [%s]: %s (InstanceID: %s, ProblemCode: %d - %s)",
					className, friendlyName, instanceID, problemCode, probDesc)

				devices = append(devices, PnPDevice{
					FriendlyName:       friendlyName,
					DeviceDesc:         deviceDesc,
					InstanceID:         instanceID,
					Class:              className,
					DriverInfPath:      infPath,
					DriverVersion:      version,
					Status:             status,
					ProblemCode:        problemCode,
					ProblemDescription: probDesc,
					IsPresent:          true,
				})
			}
		}()
	}

	deck.Infof("Total relevant PnP devices discovered: %d", len(devices))
	return devices, nil
}

func isRelevantPnPDevice(friendlyName, deviceDesc, instanceID, infPath string, classGUID *windows.GUID) bool {
	if *classGUID == guidDevClassCamera || *classGUID == guidDevClassImage {
		return true
	}
	return IsMIPICamera(friendlyName, deviceDesc, instanceID, infPath)
}

func getDeviceNames(devInfo windows.DevInfo, devInfoData *windows.DevInfoData) (friendlyName, deviceDesc string) {
	if val, err := setupDiGetDeviceProperty(devInfo, devInfoData, &devpkeyDeviceFriendlyName); err == nil {
		if s, ok := val.(string); ok && s != "" {
			friendlyName = s
		}
	}
	if val, err := setupDiGetDeviceProperty(devInfo, devInfoData, &devpkeyDeviceDeviceDesc); err == nil {
		if s, ok := val.(string); ok && s != "" {
			deviceDesc = s
		}
	}
	if friendlyName == "" {
		if val, err := setupDiGetDeviceRegistryProperty(devInfo, devInfoData, windows.SPDRP_FRIENDLYNAME); err == nil {
			if s, ok := val.(string); ok && s != "" {
				friendlyName = s
			}
		}
	}
	if deviceDesc == "" {
		if val, err := setupDiGetDeviceRegistryProperty(devInfo, devInfoData, windows.SPDRP_DEVICEDESC); err == nil {
			if s, ok := val.(string); ok && s != "" {
				deviceDesc = s
			}
		}
	}
	if friendlyName == "" {
		friendlyName = deviceDesc
	}
	return friendlyName, deviceDesc
}

func getDeviceDriverInfPath(devInfo windows.DevInfo, devInfoData *windows.DevInfoData) (string, error) {
	val, err := setupDiGetDeviceProperty(devInfo, devInfoData, &devpkeyDeviceDriverInfPath)
	if err != nil {
		return "", err
	}
	if s, ok := val.(string); ok {
		return filepath.Base(s), nil
	}
	return "", nil
}

func getDeviceDriverVersion(devInfo windows.DevInfo, devInfoData *windows.DevInfoData) (string, error) {
	val, err := setupDiGetDeviceProperty(devInfo, devInfoData, &devpkeyDeviceDriverVersion)
	if err != nil {
		return "", err
	}
	if s, ok := val.(string); ok {
		return s, nil
	}
	return "", nil
}

// Diagnose executes a comprehensive health check across Media Foundation, PnP device nodes,
// and device interfaces, returning a detailed diagnostic report with root-cause analysis
// and remediation steps for error 0xA00F4244.
func Diagnose() (*DiagnosticReport, error) {
	deck.Infof("Starting Camera Subsystem Diagnostics...")

	cameras, err := ListCameras()
	if err != nil && !IsNoCamerasAttachedError(err) {
		return nil, err
	}
	interfaces, _ := ListActiveDeviceInterfaces()
	pnpDevices, _ := ListPnPDevices()
	mipiStatus := InspectMIPISubsystem(pnpDevices)

	report := &DiagnosticReport{
		Cameras:          cameras,
		HasActiveCameras: len(cameras) > 0,
		ActiveInterfaces: interfaces,
		PnPDevices:       pnpDevices,
		MIPISubsystem:    mipiStatus,
	}

	if err != nil && IsNoCamerasAttachedError(err) {
		report.HasNoCamerasAttachedError = true
		report.ErrorCode = ErrorStringNoCamerasAttached
	}

	if report.HasActiveCameras {
		var names []string
		for _, c := range cameras {
			names = append(names, c.Name)
		}
		report.Summary = fmt.Sprintf("Camera subsystem is healthy. Found %d active video capture device(s): %s.",
			len(cameras), strings.Join(names, ", "))
		deck.Infof("Camera Diagnostics Complete: %s", report.Summary)
		return report, nil
	}

	report.HasNoCamerasAttachedError = true
	report.ErrorCode = ErrorStringNoCamerasAttached

	if len(mipiStatus.DiscoveredComponents) > 0 {
		if mipiStatus.AllComponentsHealthy && len(interfaces) == 0 {
			report.Summary = "Error 0xA00F4244 <NoCamerasAreAttached>: Internal MIPI camera PnP devices report status OK, but no active video capture interfaces are available to Windows Media Foundation. This is a known symptom of mismatched Intel MIPI camera / AVStream driver packages."
		} else if !mipiStatus.AllComponentsHealthy {
			report.Summary = fmt.Sprintf("Error 0xA00F4244 <NoCamerasAreAttached>: Internal MIPI camera components have device errors: %s.",
				strings.Join(mipiStatus.MissingOrFaulty, "; "))
		} else {
			report.Summary = "Error 0xA00F4244 <NoCamerasAreAttached>: No active camera capture streams available."
		}
	} else if len(pnpDevices) > 0 {
		report.Summary = "Error 0xA00F4244 <NoCamerasAreAttached>: PnP camera devices exist, but Media Foundation cannot enumerate active capture sources."
	} else {
		report.Summary = "Error 0xA00F4244 <NoCamerasAreAttached>: No camera hardware or PnP device nodes found on this system."
	}

	deck.Infof("Camera Diagnostics Complete: %s", report.Summary)
	return report, nil
}
