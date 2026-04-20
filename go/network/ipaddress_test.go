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

func TestGetIPAddresses(t *testing.T) {
	n, err := Connect()
	if err != nil {
		t.Fatalf("failed to connect to network: %v", err)
	}
	defer n.Close()

	// First get all IPs to find a valid address for a filter test.
	allIPs, err := n.GetIPAddresses("")
	if err != nil {
		t.Fatalf("Initial GetIPAddresses() failed: %v", err)
	}
	if len(allIPs.IPAddresses) == 0 {
		t.Skip("No IP addresses found, skipping test.")
	}
	ipToFilter := allIPs.IPAddresses[0]

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
			name:   "filter by ip address",
			filter: fmt.Sprintf("WHERE IPAddress = '%s'", ipToFilter.IPAddress),
		},
		{
			name:    "bad filter",
			filter:  "WHERE BadFilter = 'true'",
			wantErr: true,
		},
	}

	for _, tt := range testCases {
		t.Run(tt.name, func(t *testing.T) {
			ips, err := n.GetIPAddresses(tt.filter)
			if (err != nil) != tt.wantErr {
				t.Errorf("GetIPAddresses() error = %v, wantErr = %v", err, tt.wantErr)
				return
			}
			if tt.wantErr {
				return // Expected error, nothing more to check.
			}

			if len(ips.IPAddresses) == 0 {
				t.Fatal("got 0 ip addresses, want at least 1")
			}

			for _, ip := range ips.IPAddresses {
				if ip.IPAddress == "" {
					t.Error("ip has an empty IPAddress")
				}
				if ip.InterfaceIndex == 0 {
					t.Errorf("ip %q has a zero InterfaceIndex", ip.IPAddress)
				}
			}
		})
	}
}
