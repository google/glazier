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
	"testing"
)

func TestIsNoCamerasAttachedError(t *testing.T) {
	tests := []struct {
		name string
		err  error
		want bool
	}{
		{
			name: "Nil error",
			err:  nil,
			want: false,
		},
		{
			name: "Standard ErrNoCamerasAttached",
			err:  ErrNoCamerasAttached,
			want: true,
		},
		{
			name: "Custom NoCamerasAttachedError",
			err: &NoCamerasAttachedError{
				Code:    ErrorCodeNoCamerasAttached,
				Message: "custom message",
			},
			want: true,
		},
		{
			name: "Wrapped error with 0xA00F4244 in text",
			err:  errors.New("Windows Camera app failed with 0xA00F4244"),
			want: true,
		},
		{
			name: "Wrapped error with NoCamerasAreAttached text",
			err:  errors.New("Failure: NoCamerasAreAttached"),
			want: true,
		},
		{
			name: "Media Foundation 0xC00DABE0 error",
			err:  errors.New("MF error 0xC00DABE0"),
			want: true,
		},
		{
			name: "Media Foundation MF_E_NO_CAPTURE_DEVICES_AVAILABLE text",
			err:  errors.New("Error: MF_E_NO_CAPTURE_DEVICES_AVAILABLE"),
			want: true,
		},
		{
			name: "Unrelated error",
			err:  errors.New("access denied"),
			want: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := IsNoCamerasAttachedError(tt.err)
			if got != tt.want {
				t.Errorf("IsNoCamerasAttachedError(%v) = %v, want %v", tt.err, got, tt.want)
			}
		})
	}
}

func TestProblemCodeDescription(t *testing.T) {
	tests := []struct {
		code uint32
		want string
	}{
		{code: 0, want: "Device is working properly."},
		{code: 1, want: "CM_PROB_NOT_CONFIGURED: Device is not configured."},
		{code: 10, want: "CM_PROB_FAILED_START: This device cannot start (Code 10)."},
		{code: 14, want: "CM_PROB_NEED_RESTART: System restart required for this device to work (Code 14)."},
		{code: 18, want: "CM_PROB_REINSTALL: Reinstall the drivers for this device (Code 18)."},
		{code: 22, want: "CM_PROB_DISABLED: This device is disabled in Device Manager (Code 22)."},
		{code: 24, want: "CM_PROB_DEVICE_NOT_THERE: Device is not present or not working properly (Code 24)."},
		{code: 28, want: "CM_PROB_FAILED_INSTALL: The drivers for this device are not installed (Code 28)."},
		{code: 31, want: "CM_PROB_FAILED_POST_START: Windows cannot load the drivers required for this device (Code 31)."},
		{code: 39, want: "CM_PROB_DRIVER_FAILED_LOAD: Windows cannot load the device driver for this hardware (Code 39)."},
		{code: 43, want: "CM_PROB_FAILED_POST_START: Windows has stopped this device because it reported problems (Code 43)."},
		{code: 48, want: "CM_PROB_DRIVER_BLOCKED: The software for this device has been blocked from starting (Code 48)."},
		{code: 999, want: "CM Problem Code 999"},
	}

	for _, tt := range tests {
		t.Run(tt.want, func(t *testing.T) {
			got := ProblemCodeDescription(tt.code)
			if got != tt.want {
				t.Errorf("ProblemCodeDescription(%d) = %q, want %q", tt.code, got, tt.want)
			}
		})
	}
}

func TestIsMIPICamera(t *testing.T) {
	tests := []struct {
		name        string
		identifiers []string
		want        bool
	}{
		{
			name:        "Intel MTL AVStream Camera",
			identifiers: []string{"Intel(R) MTL AVStream Camera", `ACPI\INTC1070\1`, `\\?\display#...`},
			want:        true,
		},
		{
			name:        "Camera Sensor OV08X40 with ACPI OVTI08F4",
			identifiers: []string{"Integrated Camera", `ACPI\OVTI08F4\1`, "ov08x40.inf"},
			want:        true,
		},
		{
			name:        "Intel Control Logic with ACPI INT3472",
			identifiers: []string{"Intel(R) Camera Sensor Discrete", `ACPI\INT3472\0`, "iactrllogic64.inf"},
			want:        true,
		},
		{
			name:        "Intel USBIO Bridge Device",
			identifiers: []string{"Intel USBIO Bridge Device", `ACPI\INT3480\1`, "usbio.inf"},
			want:        true,
		},
		{
			name:        "Intel ISP IPU Device",
			identifiers: []string{"Intel(R) Imaging Signal Processor", `PCI\VEN_8086&DEV_7D19`, "iaisp64.inf"},
			want:        true,
		},
		{
			name:        "Generic USB UVC Webcam",
			identifiers: []string{"Logitech Webcam C920", `USB\VID_046D&PID_082D\54E343A`, `\\?\usb#vid_046d&pid_082d...`},
			want:        false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := IsMIPICamera(tt.identifiers...)
			if got != tt.want {
				t.Errorf("IsMIPICamera(%v) = %v, want %v", tt.identifiers, got, tt.want)
			}
		})
	}
}

func TestInspectMIPISubsystem(t *testing.T) {
	t.Run("Healthy subsystem", func(t *testing.T) {
		devices := []PnPDevice{
			{
				FriendlyName:       "Intel(R) MTL AVStream Camera",
				DeviceDesc:         "Intel(R) MTL AVStream Camera",
				InstanceID:         `ACPI\INTC1070\1`,
				Class:              "Camera",
				ProblemCode:        0,
				ProblemDescription: "Device is working properly.",
			},
			{
				FriendlyName:       "Camera Sensor OV08X40",
				DeviceDesc:         "Camera Sensor OV08X40",
				InstanceID:         `ACPI\OVTI08F4\1`,
				Class:              "System",
				ProblemCode:        0,
				ProblemDescription: "Device is working properly.",
			},
			{
				FriendlyName:       "Intel(R) Control Logic",
				DeviceDesc:         "Intel(R) Control Logic",
				InstanceID:         `ACPI\INT3472\1`,
				Class:              "System",
				ProblemCode:        0,
				ProblemDescription: "Device is working properly.",
			},
			{
				FriendlyName:       "Intel(R) Imaging Signal Processor",
				DeviceDesc:         "Intel(R) Imaging Signal Processor",
				InstanceID:         `PCI\VEN_8086&DEV_7D19`,
				Class:              "System",
				ProblemCode:        0,
				ProblemDescription: "Device is working properly.",
			},
		}

		status := InspectMIPISubsystem(devices)

		if !status.HasSensor {
			t.Errorf("status.HasSensor = false, want true")
		}
		if !status.HasAVStream {
			t.Errorf("status.HasAVStream = false, want true")
		}
		if !status.HasControlLogic {
			t.Errorf("status.HasControlLogic = false, want true")
		}
		if !status.HasIPU {
			t.Errorf("status.HasIPU = false, want true")
		}
		if !status.AllComponentsHealthy {
			t.Errorf("status.AllComponentsHealthy = false, want true")
		}
		if len(status.DiscoveredComponents) != 4 {
			t.Errorf("len(status.DiscoveredComponents) = %d, want 4", len(status.DiscoveredComponents))
		}
	})

	t.Run("Faulty component in subsystem", func(t *testing.T) {
		devices := []PnPDevice{
			{
				FriendlyName:       "Intel(R) MTL AVStream Camera",
				DeviceDesc:         "Intel(R) MTL AVStream Camera",
				InstanceID:         `ACPI\INTC1070\1`,
				Class:              "Camera",
				ProblemCode:        10,
				ProblemDescription: "CM_PROB_FAILED_START: This device cannot start (Code 10).",
			},
			{
				FriendlyName:       "Camera Sensor OV08X40",
				DeviceDesc:         "Camera Sensor OV08X40",
				InstanceID:         `ACPI\OVTI08F4\1`,
				Class:              "System",
				ProblemCode:        0,
				ProblemDescription: "Device is working properly.",
			},
		}

		status := InspectMIPISubsystem(devices)
		if status.AllComponentsHealthy {
			t.Errorf("status.AllComponentsHealthy = true, want false")
		}
		if len(status.MissingOrFaulty) != 1 {
			t.Errorf("len(status.MissingOrFaulty) = %d, want 1", len(status.MissingOrFaulty))
		}
	})

	t.Run("Empty devices", func(t *testing.T) {
		status := InspectMIPISubsystem(nil)
		if status.AllComponentsHealthy {
			t.Errorf("status.AllComponentsHealthy = true, want false")
		}
		if len(status.DiscoveredComponents) != 0 {
			t.Errorf("len(status.DiscoveredComponents) = %d, want 0", len(status.DiscoveredComponents))
		}
	})
}
