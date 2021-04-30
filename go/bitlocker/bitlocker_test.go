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

package bitlocker

import (
	"errors"
	"testing"

	"github.com/google/go-cmp/cmp"
	so "github.com/iamacarpet/go-win64api/shared"
)

func TestBackupToAD(t *testing.T) {
	backupErr := errors.New("backup failed")
	infoErr := errors.New("info gathering failed")
	tests := []struct {
		out        []*so.BitLockerDeviceInfo
		outBackErr error
		outInfoErr error
		wantVols   []string
		wantErr    error
	}{
		{
			out: []*so.BitLockerDeviceInfo{&so.BitLockerDeviceInfo{
				ConversionStatus:   1,
				DriveLetter:        "C:",
				PersistentVolumeID: "1-2-3-a-b-c",
			}},
			outBackErr: nil,
			outInfoErr: nil,
			wantVols:   []string{"1-2-3-a-b-c"},
			wantErr:    nil,
		},
		{ // not converted
			out: []*so.BitLockerDeviceInfo{&so.BitLockerDeviceInfo{
				ConversionStatus:   0,
				DriveLetter:        "C:",
				PersistentVolumeID: "1-2-3-a-b-c",
			}},
			outBackErr: nil,
			outInfoErr: nil,
			wantVols:   []string{},
			wantErr:    nil,
		},
		{ // skip 1
			out: []*so.BitLockerDeviceInfo{
				&so.BitLockerDeviceInfo{
					ConversionStatus:   0,
					DriveLetter:        "C:",
					PersistentVolumeID: "1-2-3-a-b-c",
				}, &so.BitLockerDeviceInfo{
					ConversionStatus:   1,
					DriveLetter:        "D:",
					PersistentVolumeID: "4-5-6-d-e-f",
				}},
			outBackErr: nil,
			outInfoErr: nil,
			wantVols:   []string{"4-5-6-d-e-f"},
			wantErr:    nil,
		},
		{ // backup err
			out: []*so.BitLockerDeviceInfo{
				&so.BitLockerDeviceInfo{
					ConversionStatus:   1,
					DriveLetter:        "C:",
					PersistentVolumeID: "1-2-3-a-b-c",
				}},
			outBackErr: backupErr,
			outInfoErr: nil,
			wantVols:   []string{"1-2-3-a-b-c"},
			wantErr:    backupErr,
		},
		{ // info err
			out: []*so.BitLockerDeviceInfo{
				&so.BitLockerDeviceInfo{
					ConversionStatus:   1,
					DriveLetter:        "C:",
					PersistentVolumeID: "1-2-3-a-b-c",
				}},
			outBackErr: nil,
			outInfoErr: infoErr,
			wantVols:   []string{"1-2-3-a-b-c"},
			wantErr:    infoErr,
		},
	}
	vols := []string{}
	for _, tt := range tests {
		funcBackup = func(arg []string) error {
			vols = arg
			return tt.outBackErr
		}
		funcRecoveryInfo = func() ([]*so.BitLockerDeviceInfo, error) {
			return tt.out, tt.outInfoErr
		}
		err := BackupToAD()
		if !cmp.Equal(vols, tt.wantVols) {
			t.Errorf("BackupToAD(%v) produced unexpected differences (-want +got): %s", tt.out, cmp.Diff(tt.wantVols, vols))
		}
		if !errors.Is(err, tt.wantErr) {
			t.Errorf("BackupToAD(%v) returned unexpected error %v", tt.out, err)
		}
	}
}
