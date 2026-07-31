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
)

func TestGetNetAdapterConfigs(t *testing.T) {
	n, err := AdapterConnect()
	if err != nil {
		t.Fatalf("failed to connect to network: %v", err)
	}
	defer n.Close()

	// First get all configs to find a valid one for a filter test.
	allConfigs, err := n.GetNetworkAdapterConfigurations("")
	if err != nil {
		t.Fatalf("Initial GetNetAdapterConfigs() failed: %v", err)
	}
	if len(allConfigs.NetworkAdapterConfigurations) == 0 {
		t.Skip("No net adapter configs found, skipping test.")
	}
	configToFilter := allConfigs.NetworkAdapterConfigurations[0]

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
			name:   "filter by interface index",
			filter: fmt.Sprintf("WHERE InterfaceIndex = %d", configToFilter.InterfaceIndex),
		},
		{
			name:    "bad filter",
			filter:  "WHERE BadFilter = 'true'",
			wantErr: true,
		},
	}

	for _, tt := range testCases {
		t.Run(tt.name, func(t *testing.T) {
			configs, err := n.GetNetworkAdapterConfigurations(tt.filter)
			if (err != nil) != tt.wantErr {
				t.Errorf("GetNetAdapterConfigs() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			if tt.wantErr {
				return // Expected error, nothing more to check.
			}

			if len(configs.NetworkAdapterConfigurations) == 0 {
				t.Fatal("got 0 net adapter configs, want at least 1")
			}
		})
	}
}
