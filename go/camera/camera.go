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

// Package camera provides capabilities to enumerate, inspect, and diagnose
// active cameras and video capture devices on Windows without activating
// hardware sensors or illuminating privacy indicator LEDs.
//
// It specifically addresses Windows Camera error 0xA00F4244 (NoCamerasAreAttached)
// and internal MIPI / CSI camera issues where PnP device nodes report "OK"
// but Windows Media Foundation / capture APIs cannot find active cameras.
package camera

import (
	"errors"
	"fmt"
	"strings"
)

const (
	// ErrorCodeNoCamerasAttached is the Windows Camera error code 0xA00F4244
	// (also known as 0xA00F4244 <NoCamerasAreAttached>).
	ErrorCodeNoCamerasAttached uint32 = 0xA00F4244

	// HResultNoCamerasAttached is the signed 32-bit HRESULT representation of 0xA00F4244 (-1609612732).
	HResultNoCamerasAttached int32 = -1609612732

	// ErrorStringNoCamerasAttached is the string hex representation.
	ErrorStringNoCamerasAttached = "0xA00F4244"
)

// NoCamerasAttachedError represents the Windows Camera error 0xA00F4244.
type NoCamerasAttachedError struct {
	Code    uint32
	HResult int32
	Message string
}

func (e *NoCamerasAttachedError) Error() string {
	return fmt.Sprintf("camera error 0x%08X: %s", e.Code, e.Message)
}

// ErrNoCamerasAttached indicates that Windows Media Foundation found no active
// video capture devices attached to the system (error 0xA00F4244 <NoCamerasAreAttached>).
var ErrNoCamerasAttached = &NoCamerasAttachedError{
	Code:    ErrorCodeNoCamerasAttached,
	HResult: HResultNoCamerasAttached,
	Message: "No cameras are attached or active (0xA00F4244 <NoCamerasAreAttached>)",
}

// ErrUnsupportedPlatform is returned when running camera Win32 queries on non-Windows platforms.
var ErrUnsupportedPlatform = errors.New("camera Win32 API is only supported on Windows")

// IsNoCamerasAttachedError returns true if the given error corresponds to 0xA00F4244
// or Media Foundation error MF_E_NO_CAPTURE_DEVICES_AVAILABLE (0xC00DABE0).
func IsNoCamerasAttachedError(err error) bool {
	if err == nil {
		return false
	}
	var ncaErr *NoCamerasAttachedError
	if errors.As(err, &ncaErr) {
		return ncaErr.Code == ErrorCodeNoCamerasAttached
	}
	if errors.Is(err, ErrNoCamerasAttached) {
		return true
	}
	errLower := strings.ToLower(err.Error())
	return strings.Contains(errLower, "0xa00f4244") ||
		strings.Contains(errLower, "nocamerasareattached") ||
		strings.Contains(errLower, "0xc00dabe0") ||
		strings.Contains(errLower, "mf_e_no_capture_devices_available")
}

// CameraInfo contains information about an active video capture source.
type CameraInfo struct {
	// Name is the friendly display name (e.g. "Intel(R) MTL AVStream Camera" or "Integrated Camera").
	Name string `json:"name"`
	// SymbolicLink is the PnP device interface symbolic link path.
	SymbolicLink string `json:"symbolic_link"`
	// DevicePath is the device instance path or provider path.
	DevicePath string `json:"device_path"`
	// IsMIPI indicates if this is an internal MIPI CSI / AVStream camera.
	IsMIPI bool `json:"is_mipi"`
	// HardwareSource indicates if the source is backed by physical hardware.
	HardwareSource bool `json:"hardware_source"`
	// Category is the category GUID string.
	Category string `json:"category"`
}

// PnPDevice represents a camera, sensor, or imaging device node in the Windows PnP tree.
type PnPDevice struct {
	FriendlyName       string `json:"friendly_name"`
	DeviceDesc         string `json:"device_desc"`
	InstanceID         string `json:"instance_id"`
	Class              string `json:"class"`
	DriverInfPath      string `json:"driver_inf_path,omitempty"`
	DriverVersion      string `json:"driver_version,omitempty"`
	Status             uint32 `json:"status"`
	ProblemCode        uint32 `json:"problem_code"`
	ProblemDescription string `json:"problem_description,omitempty"`
	IsPresent          bool   `json:"is_present"`
}

// MIPISubsystemStatus contains health and presence status for internal MIPI camera components.
type MIPISubsystemStatus struct {
	// HasSensor indicates if a MIPI camera sensor (e.g. OV08X40, VD55G0, Omnivision, Sony) is in the PnP tree.
	HasSensor bool `json:"has_sensor"`
	// HasIPU indicates if the Intel Image Processing Unit (ISP / Control Logic) is present in the PnP tree.
	HasIPU bool `json:"has_ipu"`
	// HasAVStream indicates if the virtual AVStream camera filter is present in the PnP tree.
	HasAVStream bool `json:"has_avstream"`
	// HasControlLogic indicates if Intel Control Logic / Flash LED device is present.
	HasControlLogic bool `json:"has_control_logic"`
	// AllComponentsHealthy is true if all discovered MIPI components report ProblemCode 0 (OK).
	AllComponentsHealthy bool `json:"all_components_healthy"`
	// DiscoveredComponents lists all discovered MIPI-related PnP devices.
	DiscoveredComponents []PnPDevice `json:"discovered_components"`
	// MissingOrFaulty lists descriptions of missing or broken parts of the MIPI pipeline.
	MissingOrFaulty []string `json:"missing_or_faulty,omitempty"`
}

// DiagnosticReport is a comprehensive health check and diagnostic report for system cameras.
type DiagnosticReport struct {
	// Cameras is the list of active video capture devices enumerated by Windows Media Foundation.
	Cameras []CameraInfo `json:"cameras"`
	// HasActiveCameras is true if at least one active video capture source is present.
	HasActiveCameras bool `json:"has_active_cameras"`
	// HasNoCamerasAttachedError is true if the system exhibits error 0xA00F4244.
	HasNoCamerasAttachedError bool `json:"has_no_cameras_attached_error"`
	// ErrorCode is "0xA00F4244" if in error state, or empty.
	ErrorCode string `json:"error_code,omitempty"`
	// ActiveInterfaces lists device interface paths matching KSCATEGORY_VIDEO_CAMERA / KSCATEGORY_CAPTURE.
	ActiveInterfaces []string `json:"active_interfaces"`
	// PnPDevices lists all camera/imaging/sensor devices found in the PnP tree.
	PnPDevices []PnPDevice `json:"pnp_devices"`
	// MIPISubsystem details the state of internal MIPI camera drivers and devices.
	MIPISubsystem MIPISubsystemStatus `json:"mipi_subsystem"`
	// Summary is a human-readable diagnostic analysis.
	Summary string `json:"summary"`
}

// Known MIPI camera driver patterns and device identifiers.
var mipiDevicePatterns = []string{
	"avstream",
	"ov08x40",
	"ovti08f4",
	"ovti08x4",
	"ovti",
	"vd55g0",
	"vd55g1",
	"vd55g",
	"iacamera",
	"iaisp",
	"iactrllogic",
	"iaflash",
	"intc1070",
	"intc1020",
	"intc1065",
	"intc1095",
	"int3470",
	"int3471",
	"int3472",
	"int3474",
	"int3477",
	"int347e",
	"int3480",
	"int3482",
	"hm2170",
	"hm11b1",
	"hi556",
	"imx",
	"gc5035",
	"ov2740",
	"ov9734",
	"ov8856",
	"mipi",
	"intel(r) mtl avstream",
	"intel(r) ptl avstream",
	"intel(r) lnl avstream",
	"intel(r) control logic",
	"intel(r) imaging signal processor",
	"intel(r) camera flash led",
	"intel(r) usbi2c",
	"intel(r) usbgpio",
	"intel(r) usbio",
	"intel usbio bridge",
	"usbi2c",
	"usbgpio",
	"usbio bridge",
	"camera sensor",
	"7d19",
	"645d",
	"465d",
	"a75d",
	"9a19",
	"b719",
}

// IsMIPICamera returns true if any passed identifier matches known MIPI camera components.
func IsMIPICamera(identifiers ...string) bool {
	for _, id := range identifiers {
		if id == "" {
			continue
		}
		lower := strings.ToLower(id)
		for _, pat := range mipiDevicePatterns {
			if strings.Contains(lower, pat) {
				return true
			}
		}
	}
	return false
}

// InspectMIPISubsystem checks the presence and status of internal MIPI camera components from PnP devices.
func InspectMIPISubsystem(pnpDevices []PnPDevice) MIPISubsystemStatus {
	var status MIPISubsystemStatus
	allHealthy := true

	for _, dev := range pnpDevices {
		if !IsMIPICamera(dev.FriendlyName, dev.DeviceDesc, dev.InstanceID, dev.DriverInfPath) {
			continue
		}

		status.DiscoveredComponents = append(status.DiscoveredComponents, dev)

		combined := strings.ToLower(fmt.Sprintf("%s %s %s %s", dev.FriendlyName, dev.DeviceDesc, dev.InstanceID, dev.DriverInfPath))

		if strings.Contains(combined, "sensor") || strings.Contains(combined, "ov08x40") || strings.Contains(combined, "ovti") || strings.Contains(combined, "vd55g") || strings.Contains(combined, "hm11b") || strings.Contains(combined, "hm217") || strings.Contains(combined, "hi556") || strings.Contains(combined, "imx") || strings.Contains(combined, "gc5035") || strings.Contains(combined, "ov2740") || strings.Contains(combined, "ov9734") || strings.Contains(combined, "ov8856") || strings.Contains(combined, "int3472") || strings.Contains(combined, "int3474") {
			status.HasSensor = true
		}
		if strings.Contains(combined, "imaging signal processor") || strings.Contains(combined, "iaisp") || strings.Contains(combined, "ipu") || strings.Contains(combined, "7d19") || strings.Contains(combined, "645d") || strings.Contains(combined, "465d") || strings.Contains(combined, "a75d") || strings.Contains(combined, "9a19") || strings.Contains(combined, "b719") {
			status.HasIPU = true
		}
		if strings.Contains(combined, "avstream") || strings.Contains(combined, "iacamera") || strings.Contains(combined, "intc1070") || strings.Contains(combined, "intc1020") || strings.Contains(combined, "intc1065") || strings.Contains(combined, "intc1095") {
			status.HasAVStream = true
		}
		if strings.Contains(combined, "control logic") || strings.Contains(combined, "iactrllogic") || strings.Contains(combined, "flash") || strings.Contains(combined, "iaflash") || strings.Contains(combined, "int3480") || strings.Contains(combined, "int3482") || strings.Contains(combined, "usbi2c") || strings.Contains(combined, "usbgpio") || strings.Contains(combined, "usbio") {
			status.HasControlLogic = true
		}

		if dev.ProblemCode != 0 {
			allHealthy = false
			displayName := dev.FriendlyName
			if displayName == "" {
				displayName = dev.DeviceDesc
			}
			if displayName == "" {
				displayName = dev.InstanceID
			}
			status.MissingOrFaulty = append(status.MissingOrFaulty, fmt.Sprintf("%s (%s): %s", displayName, dev.InstanceID, dev.ProblemDescription))
		}
	}

	status.AllComponentsHealthy = allHealthy && len(status.DiscoveredComponents) > 0
	return status
}

// ProblemCodeDescription returns a human-readable string for Windows ConfigMgr (CM) problem numbers.
func ProblemCodeDescription(problemCode uint32) string {
	switch problemCode {
	case 0:
		return "Device is working properly."
	case 1:
		return "CM_PROB_NOT_CONFIGURED: Device is not configured."
	case 10:
		return "CM_PROB_FAILED_START: This device cannot start (Code 10)."
	case 14:
		return "CM_PROB_NEED_RESTART: System restart required for this device to work (Code 14)."
	case 18:
		return "CM_PROB_REINSTALL: Reinstall the drivers for this device (Code 18)."
	case 22:
		return "CM_PROB_DISABLED: This device is disabled in Device Manager (Code 22)."
	case 24:
		return "CM_PROB_DEVICE_NOT_THERE: Device is not present or not working properly (Code 24)."
	case 28:
		return "CM_PROB_FAILED_INSTALL: The drivers for this device are not installed (Code 28)."
	case 31:
		return "CM_PROB_FAILED_POST_START: Windows cannot load the drivers required for this device (Code 31)."
	case 39:
		return "CM_PROB_DRIVER_FAILED_LOAD: Windows cannot load the device driver for this hardware (Code 39)."
	case 43:
		return "CM_PROB_FAILED_POST_START: Windows has stopped this device because it reported problems (Code 43)."
	case 48:
		return "CM_PROB_DRIVER_BLOCKED: The software for this device has been blocked from starting (Code 48)."
	default:
		return fmt.Sprintf("CM Problem Code %d", problemCode)
	}
}
