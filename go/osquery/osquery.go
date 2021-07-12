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

// Package osquery provides helpers for managing osquery.
package osquery

import (
	"fmt"
	"os"
	"regexp"
	"time"

	"github.com/google/logger"
	"github.com/google/glazier/go/helpers"
)

const (
	dbPath    = `C:\ProgramData\osquery\osquery.db`
	serviceID = "osqueryd"
)

// ResetDB attempts to stop the osquery service and remove the osquery database file.
func ResetDB(restart bool) error {
	if _, ok := os.Stat(dbPath); ok != nil {
		return fmt.Errorf("Cannot delete OSquery database because it was not found: %s", dbPath)
	}

	logger.Info("Stopping osquery service.")
	if err := Stop(); err != nil {
		return err
	}

	logger.Infof("Database found, deleting current database: %s", dbPath)
	if err := os.RemoveAll(dbPath); err != nil {
		return fmt.Errorf("Failed to delete the OSquery database: %w", err)
	}

	if !restart {
		return nil
	}

	return Start()
}

// Restart attempts to restart the osquery service.
func Restart() error {
	// Stop() waits for the service to shutdown completely before returning.
	if err := Stop(); err != nil {
		return err
	}
	return Start()
}

// Start attempts to start the osquery service.
func Start() error {
	return helpers.StartService(serviceID)
}

// Stop attempts to stop the osquery service.
//
// The osqueryd and extension processes don't stop immediately, so restarting the service
// (or stopping and starting it right away) could lead to zombie processes that maintain a DB lock
// and cause subsequent processes to fail.
func Stop() error {
	if err := helpers.StopService(serviceID); err != nil {
		return fmt.Errorf("helpers.StopService: %w", err)
	}

	// Wait for osqueryd and extensions to shut down cleanly. DB files will be locked until processes exit.
	// TODO(b/192259933): Remove this timeout after confirming the new OSQuery shutdown process is working properly
	re := regexp.MustCompile("osquery*")
	if err := helpers.WaitForProcessExit(re, 5*time.Minute); err != nil {
		return fmt.Errorf("helpers.WaitForProcessExit: %w", err)
	}
	return nil
}
