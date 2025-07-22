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

import (
	"net"
	"testing"

	"github.com/google/go-cmp/cmp"
	"golang.org/x/sys/windows"
)

func TestNetworkAdapterPropertiesByMac(t *testing.T) {
	adapters, err := ListLocalInterfaces(GAAFlagIncludeAllInterfaces)
	if err != nil {
		t.Fatalf("ListLocalInterfaces() failed: %v", err)
	}
	if len(adapters) == 0 {
		t.Skip("No network adapters found on this system.")
	}

	// Use a known adapter mac from the test VM.
	var adapterMAC string
	for _, adapter := range adapters {
		if adapter.PhysicalAddressLength > 0 {
			mac := net.HardwareAddr(adapter.PhysicalAddress[:adapter.PhysicalAddressLength])
			adapterMAC = mac.String()
			break
		}
	}

	if adapterMAC == "" {
		t.Skip("No network adapters with a physical address found on this system.")
	}

	tests := []struct {
		name    string
		mac     string
		wantErr bool
	}{
		{
			name: "success",
			mac:  adapterMAC,
		},
		{
			name:    "failure",
			mac:     "DE:AD:BE:EF:CA:FE",
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			adapter, err := NetworkAdapterPropertiesByMac(GAAFlagIncludeAllInterfaces, tt.mac)
			if (err != nil) != tt.wantErr {
				t.Errorf("NetworkAdapterPropertiesByMac() error = %v, wantErr = %v", err, tt.wantErr)
				return
			}
			if tt.wantErr {
				return // Expected error, nothing more to check.
			}
			mac := net.HardwareAddr(adapter.PhysicalAddress[:adapter.PhysicalAddressLength])
			if diff := cmp.Diff(tt.mac, mac.String()); diff != "" {
				t.Errorf("NetworkAdapterPropertiesByMac(%q) returned diff (-want +got):\n%s", tt.mac, diff)
			}
		})
	}
}

func TestNetworkAdapterProperties(t *testing.T) {
	adapters, err := ListLocalInterfaces(GAAFlagIncludeAllInterfaces)
	if err != nil {
		t.Fatalf("ListLocalInterfaces() failed: %v", err)
	}
	if len(adapters) == 0 {
		t.Skip("No network adapters found on this system.")
	}

	// Use a known adapter name from the test VM
	adapterName := windows.BytePtrToString(adapters[0].AdapterName)

	tests := []struct {
		name    string
		adapter string
		wantErr bool
	}{
		{
			name:    "success",
			adapter: adapterName,
		},
		{
			name:    "failure",
			adapter: "the-nic-is-a-lie",
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			adapter, err := NetworkAdapterProperties(GAAFlagIncludeAllInterfaces, tt.adapter)
			if (err != nil) != tt.wantErr {
				t.Errorf("NetworkAdapterProperties() error = %v, wantErr = %v", err, tt.wantErr)
				return
			}
			if tt.wantErr {
				return // Expected error, nothing more to check.
			}
			if diff := cmp.Diff(tt.adapter, windows.BytePtrToString(adapter.AdapterName)); diff != "" {
				t.Errorf("NetworkAdapterProperties(%q) returned diff (-want +got):\n%s", tt.adapter, diff)
			}
		})
	}
}
