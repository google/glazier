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

// Package bitlocker provides functionality for managing Bitlocker.
package bitlocker

import (
	"github.com/google/logger"
	"github.com/iamacarpet/go-win64api"
)

var (
	// Test Helpers
	funcBackup       = winapi.BackupBitLockerRecoveryKeys
	funcRecoveryInfo = winapi.GetBitLockerRecoveryInfo
)

// BackupToAD backs up Bitlocker recovery keys to Active Directory.
func BackupToAD() error {
	infos, err := funcRecoveryInfo()
	if err != nil {
		return err
	}
	volIDs := []string{}
	for _, i := range infos {
		if i.ConversionStatus != 1 {
			logger.Warningf("Skipping volume %s due to conversion status (%d).", i.DriveLetter, i.ConversionStatus)
			continue
		}
		logger.Infof("Backing up Bitlocker recovery password for drive %q.", i.DriveLetter)
		volIDs = append(volIDs, i.PersistentVolumeID)
	}
	return funcBackup(volIDs)
}
