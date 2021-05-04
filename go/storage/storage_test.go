// Copyright 2021 Google LLC
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

package storage

import (
	"errors"
	"fmt"

	"io/ioutil"
	"testing"

	"github.com/google/go-cmp/cmp"
	"github.com/google/winops/powershell"
)

const (
	testData = "testdata"
)

func TestGetPartitionInfo(t *testing.T) {
	tests := []struct {
		psOut   string
		want    *PartitionInfo
		psErr   error
		wantErr error
	}{
		{"partinfo.txt",
			&PartitionInfo{
				GUID:            "{09eb89b8-1595-4b70-b056-a3adbbb33255}",
				PartitionNumber: 1,
				Size:            524288000,
				Type:            "Recovery"},
			nil, nil,
		},
		{"invalid.txt",
			&PartitionInfo{},
			nil, ErrUnmarshal,
		},
	}
	for i, tt := range tests {
		t.Run(fmt.Sprintf("Test%d", i), func(t *testing.T) {
			fnPSCmd = func(psCmd string, s []string, c *powershell.PSConfig) ([]byte, error) {
				p := fmt.Sprintf("%s/%s", testData, tt.psOut)
				var body []byte
				var err error
				if tt.psOut != "" {
					if body, err = ioutil.ReadFile(p); err != nil {
						t.Errorf("ioutil.ReadFile(%s) produced error %v", p, err)
					}
				}
				return body, tt.psErr
			}
			got, err := GetPartitionInfo(0, 1)
			if diff := cmp.Diff(tt.want, got); diff != "" {
				{
					t.Errorf("GetPartitionInfo(%v) returned unexpected diff (-want +got):\n%s", tt.psOut, diff)
				}
				if !errors.Is(err, tt.wantErr) {
					t.Errorf("GetPartitionInfo(%v) returned unexpected error %v", tt.psOut, err)
				}
			}
		})
	}
}

func TestGetPartitionSupportedSize(t *testing.T) {
	tests := []struct {
		psOut   string
		want    *PartitionSupportedSize
		psErr   error
		wantErr error
	}{
		{`{
    "SizeMin":  524288000,
    "SizeMax":  524288000
		}`,
			&PartitionSupportedSize{SizeMin: 524288000, SizeMax: 524288000},
			nil, nil,
		},
		{`{
    "Invalid":  524288000,
		}`,
			&PartitionSupportedSize{},
			nil, ErrUnmarshal,
		},
	}
	for i, tt := range tests {
		t.Run(fmt.Sprintf("Test%d", i), func(t *testing.T) {
			fnPSCmd = func(psCmd string, s []string, c *powershell.PSConfig) ([]byte, error) {
				return []byte(tt.psOut), tt.psErr
			}
			got, err := GetPartitionSupportedSize(0, 1)
			if diff := cmp.Diff(tt.want, got); diff != "" {
				{
					t.Errorf("GetPartitionSupportedSize(%v) returned unexpected diff (-want +got):\n%s", tt.psOut, diff)
				}
				if !errors.Is(err, tt.wantErr) {
					t.Errorf("GetPartitionSupportedSize(%v) returned unexpected error %v", tt.psOut, err)
				}
			}
		})
	}
}
