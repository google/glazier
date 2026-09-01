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
// It specifically addresses Windows Camera error 0xA00F4244
// (NoCamerasAreAttached) and internal MIPI / CSI camera issues where PnP
// device nodes report "OK" but Windows Media Foundation / capture APIs cannot
// find active cameras.
package camera

import (
	"errors"
	"fmt"
	"strings"
)

const (
	// ErrorCodeNoCamerasAttached is the Windows Camera error code 0xA00F4244 (also known as 0xA00F4244 <NoCamerasAreAttached>).
	ErrorCodeNoCamerasAttached uint32 = 0xA00F4244

	// HResultNoCamerasAttached is the signed 32-bit HRESULT representation of 0xA00F4244 (-1609612732).
	HResultNoCamerasAttached int32 = -1609612732

	// ErrorStringNoCamerasAttached is the string hex representation.
	ErrorStringNoCamerasAttached = "0xA00F4244"

	// ProblemDescOK indicates the device is working properly.
	ProblemDescOK = "Device is working properly."
	// ProblemDescNotConfigured indicates the device is not configured.
	ProblemDescNotConfigured = "CM_PROB_NOT_CONFIGURED: Device is not configured."
	// ProblemDescFailedStart indicates the device cannot start (Code 10).
	ProblemDescFailedStart = "CM_PROB_FAILED_START: This device cannot start (Code 10)."
	// ProblemDescNeedRestart indicates a restart is required for the device (Code 14).
	ProblemDescNeedRestart = "CM_PROB_NEED_RESTART: System restart required for this device to work (Code 14)."
	// ProblemDescReinstall indicates drivers must be reinstalled for the device (Code 18).
	ProblemDescReinstall = "CM_PROB_REINSTALL: Reinstall the drivers for this device (Code 18)."
	// ProblemDescDisabled indicates the device is disabled in Device Manager (Code 22).
	ProblemDescDisabled = "CM_PROB_DISABLED: This device is disabled in Device Manager (Code 22)."
	// ProblemDescDeviceNotThere indicates the device is not present (Code 24).
	ProblemDescDeviceNotThere = "CM_PROB_DEVICE_NOT_THERE: Device is not present or not working properly (Code 24)."
	// ProblemDescFailedInstall indicates drivers are not installed (Code 28).
	ProblemDescFailedInstall = "CM_PROB_FAILED_INSTALL: The drivers for this device are not installed (Code 28)."
	// ProblemDescFailedPostStart indicates Windows cannot load the drivers (Code 31).
	ProblemDescFailedPostStart = "CM_PROB_FAILED_POST_START: Windows cannot load the drivers required for this device (Code 31)."
	// ProblemDescDriverFailedLoad indicates Windows cannot load the device driver (Code 39).
	ProblemDescDriverFailedLoad = "CM_PROB_DRIVER_FAILED_LOAD: Windows cannot load the device driver for this hardware (Code 39)."
	// ProblemDescCode43Stopped indicates Windows stopped the device due to problems (Code 43).
	ProblemDescCode43Stopped = "CM_PROB_FAILED_POST_START: Windows has stopped this device because it reported problems (Code 43)."
	// ProblemDescDriverBlocked indicates the driver software has been blocked (Code 48).
	ProblemDescDriverBlocked = "CM_PROB_DRIVER_BLOCKED: The software for this device has been blocked from starting (Code 48)."
)

var (
	// ErrNoCamerasAttached indicates that Windows Media Foundation found no active
	// video capture devices attached to the system (error 0xA00F4244
	// <NoCamerasAreAttached>).
	ErrNoCamerasAttached = &NoCamerasAttachedError{
		Code:    ErrorCodeNoCamerasAttached,
		HResult: HResultNoCamerasAttached,
		Message: "No cameras are attached or active (0xA00F4244 <NoCamerasAreAttached>)",
	}

	// ErrUnsupportedPlatform is returned when running camera Win32 queries on non-Windows platforms.
	ErrUnsupportedPlatform = errors.New("camera Win32 API is only supported on Windows")
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

// IsNoCamerasAttachedError returns true if the given error corresponds to
// 0xA00F4244 or Media Foundation error MF_E_NO_CAPTURE_DEVICES_AVAILABLE
// (0xC00DABE0).
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

// Info contains information about an active video capture source.
type Info struct {
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
	Cameras []Info `json:"cameras"`
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

// IsMIPICamera returns true if any passed identifier matches known MIPI camera components.
func IsMIPICamera(identifiers ...string) bool {
	for _, id := range identifiers {
		if id == "" {
			continue
		}
		lower := strings.ToLower(id)
		if _, ok := mipiDevicePatterns[lower]; ok {
			return true
		}
		for pat := range mipiDevicePatterns {
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

		if isSensor(combined) {
			status.HasSensor = true
		}
		if isIPU(combined) {
			status.HasIPU = true
		}
		if isAVStream(combined) {
			status.HasAVStream = true
		}
		if isControlLogic(combined) {
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
			status.MissingOrFaulty = append(
				status.MissingOrFaulty,
				fmt.Sprintf("%s (%s): %s",
					displayName,
					dev.InstanceID,
					dev.ProblemDescription,
				),
			)
		}
	}

	status.AllComponentsHealthy = allHealthy &&
		len(status.DiscoveredComponents) > 0
	return status
}

// ProblemCodeDescription returns a human-readable string for Windows ConfigMgr (CM) problem numbers.
func ProblemCodeDescription(problemCode uint32) string {
	switch problemCode {
	case 0:
		return ProblemDescOK
	case 1:
		return ProblemDescNotConfigured
	case 10:
		return ProblemDescFailedStart
	case 14:
		return ProblemDescNeedRestart
	case 18:
		return ProblemDescReinstall
	case 22:
		return ProblemDescDisabled
	case 24:
		return ProblemDescDeviceNotThere
	case 28:
		return ProblemDescFailedInstall
	case 31:
		return ProblemDescFailedPostStart
	case 39:
		return ProblemDescDriverFailedLoad
	case 43:
		return ProblemDescCode43Stopped
	case 48:
		return ProblemDescDriverBlocked
	default:
		return fmt.Sprintf("CM Problem Code %d", problemCode)
	}
}
