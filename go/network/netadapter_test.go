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
	"testing"

	"golang.org/x/sys/windows"
)

func TestGetNetAdapters(t *testing.T) {
	n, err := Connect()
	if err != nil {
		t.Fatalf("failed to connect to network: %v", err)
	}
	defer n.Close()

	// First get all adapters to find a valid name for a filter test.
	allAdapters, err := n.GetNetAdapters("")
	if err != nil {
		t.Fatalf("Initial GetNetAdapters() failed: %v", err)
	}
	if len(allAdapters.NetAdapters) == 0 {
		t.Skip("No network adapters found, skipping test.")
	}
	adapterToFilter := allAdapters.NetAdapters[0]

	testCases := []struct {
		name    string
		filter  string
		wantErr bool
	}{
		{
			name:   "no filter",
			filter: "",
		},
		{
			name:   "filter by name",
			filter: fmt.Sprintf("WHERE Name = '%s'", adapterToFilter.Name),
		},
		{
			name:    "bad filter",
			filter:  fmt.Sprintf("WHERE OS = 'MacOS'"),
			wantErr: true,
		},
	}

	for _, tt := range testCases {
		t.Run(tt.name, func(t *testing.T) {
			adapters, err := n.GetNetAdapters(tt.filter)
			if (err != nil) != tt.wantErr {
				t.Errorf("GetNetAdapters() error = %v, wantErr = %v", err, tt.wantErr)
				return
			}
			if tt.wantErr {
				return // Expected error, nothing more to check.
			}

			if len(adapters.NetAdapters) == 0 {
				t.Fatal("got 0 adapters, want at least 1")
			}

			for _, adapter := range adapters.NetAdapters {
				if adapter.Name == "" {
					t.Error("adapter has an empty Name")
				}
				if adapter.InterfaceDescription == "" {
					t.Errorf("adapter %q has an empty InterfaceDescription", adapter.Name)
				}
				if adapter.InterfaceGUID == (windows.GUID{}) {
					t.Errorf("adapter %q has a zero InterfaceGUID", adapter.Name)
				}
			}
		})
	}
}

func TestRenameAdapter(t *testing.T) {
	n, err := Connect()
	if err != nil {
		t.Fatalf("failed to connect to network: %v", err)
	}
	defer n.Close()
	adapters, err := n.GetNetAdapters("")
	if err != nil {
		t.Fatalf("GetNetAdapters() failed: %v", err)
	}

	if len(adapters.NetAdapters) == 0 {
		t.Fatal("GetNetAdapters() returned no adapters, cannot test rename.")
	}

	adapterToTest := &adapters.NetAdapters[0]

	testCases := []struct {
		name     string
		testName string
		wantErr  bool
	}{
		{
			name:     "simple rename",
			testName: "cider-test-adapter",
		},
		{
			name:     "empty name",
			testName: "",
			wantErr:  true,
		},
	}

	for _, tt := range testCases {
		t.Run(tt.name, func(t *testing.T) {
			// Get the current state of the adapter to have the correct original name for cleanup.
			currentAdapterState, err := findAdapterByGUID(t, n, adapterToTest.InterfaceGUID)
			if err != nil {
				t.Fatalf("Could not find adapter by GUID before renaming: %v", err)
			}
			originalName := currentAdapterState.Name

			// Defer cleanup to restore the original name at the end of the sub-test.
			defer func() {
				adapterForCleanup, findErr := findAdapterByGUID(t, n, adapterToTest.InterfaceGUID)
				if findErr != nil {
					t.Logf("Could not find adapter for cleanup: %v", findErr)
					return
				}
				if err := adapterForCleanup.Rename(originalName); err != nil {
					t.Errorf("Failed to rename adapter back to %q: %v", originalName, err)
				}
			}()

			err = currentAdapterState.Rename(tt.testName)
			if (err != nil) != tt.wantErr {
				t.Fatalf("Rename() error = %v, wantErr %v", err, tt.wantErr)
			}
			if tt.wantErr {
				return // Expected error, nothing more to check.
			}

			// Verify the rename worked.
			renamedAdapter, err := findAdapterByGUID(t, n, adapterToTest.InterfaceGUID)
			if err != nil {
				t.Fatalf("Could not find adapter by GUID after renaming: %v", err)
			}
			if renamedAdapter.Name != tt.testName {
				t.Errorf("adapter name is %q, want %q", renamedAdapter.Name, tt.testName)
			}
		})
	}
}

// findAdapterByGUID is a helper to find a specific network adapter.
func findAdapterByGUID(t *testing.T, n Service, guid windows.GUID) (*NetAdapter, error) {
	t.Helper()
	adapters, err := n.GetNetAdapters("")
	if err != nil {
		return nil, fmt.Errorf("GetNetAdapters() failed: %w", err)
	}
	for i := range adapters.NetAdapters {
		if adapters.NetAdapters[i].InterfaceGUID == guid {
			return &adapters.NetAdapters[i], nil
		}
	}
	return nil, fmt.Errorf("adapter with GUID %s not found", guid)
}

func TestEnableAlreadyEnabledAdapter(t *testing.T) {
	n, err := Connect()
	if err != nil {
		t.Fatalf("failed to connect to network: %v", err)
	}
	defer n.Close()

	// Filter for enabled adapters using InterfaceAdminStatus = 1 (Up).
	adapters, err := n.GetNetAdapters("WHERE InterfaceAdminStatus = 1")
	if err != nil {
		t.Fatalf("GetNetAdapters() failed: %v", err)
	}
	if len(adapters.NetAdapters) == 0 {
		t.Skip("No enabled network adapters found, skipping test.")
	}

	adapter := adapters.NetAdapters[0]
	t.Logf("Attempting to enable already enabled adapter: %s", adapter.Name)

	// Calling Enable on an already enabled adapter should be a no-op and not return an error.
	if err := adapter.Enable(); err != nil {
		t.Errorf("Enable() on already enabled adapter returned an error: %v", err)
	}
}
