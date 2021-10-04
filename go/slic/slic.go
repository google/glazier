// Copyright 2020 Google LLC
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

//go:build windows
// +build windows

// Package slic provides helpers for interacting with the oa3tool binary.
// https://docs.microsoft.com/en-us/windows-hardware/manufacture/desktop/oem-activation-3
// https://docs.microsoft.com/en-us/windows-hardware/manufacture/desktop/oa3-using-on-factory-floor
package slic

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/google/logger"
	"github.com/google/glazier/go/helpers"
)

// CheckLicense validates whether the system is licensed to run Windows.
func CheckLicense(slicBinary string) error {
	logger.Info("Checking whether system is licensed to run Windows...")

	if slicBinary == "" {
		slicBinary = filepath.Join(filepath.Join(os.Getenv("SystemDrive"), `\oa3tool.exe`))
	}
	out, err := helpers.Exec(slicBinary, []string{"/validate"}, nil)

	if err != nil {
		return fmt.Errorf("helpers.Exec(%s): %w", slicBinary, err)
	}

	if out.ExitCode != 0 {
		logger.Warningf("%q Stderr:\n%s", slicBinary, string(out.Stderr))
		return fmt.Errorf(fmt.Sprintf("failed to execute %q. Exit code: %d", slicBinary, out.ExitCode))
	}

	logger.Info("System is licensed to run Windows.")

	return nil
}
