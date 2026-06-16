//go:build windows

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

package lockscreenui

import (
	"golang.org/x/net/context"
	"os"
	"path/filepath"
	"testing"
)

func TestUpdateProgressGeneration(t *testing.T) {
	ctx := context.Background()
	outDir := os.Getenv("TEST_UNDECLARED_OUTPUTS_DIR")
	if outDir == "" {
		outDir = t.TempDir()
	}

	tempScreensDir := filepath.Join(outDir, "generated_screens")
	if err := os.MkdirAll(tempScreensDir, 0755); err != nil {
		t.Fatalf("MkdirAll failed: %v", err)
	}

	cfg := Config{
		TempDir:     tempScreensDir,
		TitlePrefix: "Provisioning: ",
		FooterText:  "System setup in progress - please wait",
	}

	ui, err := NewProvisioningUI(ctx, cfg)
	if err != nil {
		t.Fatalf("NewProvisioningUI failed: %v", err)
	}

	testMsg := "Stage 1 of 7: Initializing system and resizing disk..."
	if err := ui.UpdateLockScreen(ctx, 1, testMsg); err != nil {
		t.Logf("UpdateLockScreen note: %v", err)
	}

	expectedImagePath := filepath.Join(tempScreensDir, "step_1.png")
	if _, err := os.Stat(expectedImagePath); os.IsNotExist(err) {
		t.Fatalf("Image artifact %s not generated, want it to exist", expectedImagePath)
	}

	t.Logf("Successfully generated image artifact at: %s (preserved for Sponge download)", expectedImagePath)

	cleanupTestDir := filepath.Join(outDir, "cleanup_test_screens")
	if err := os.MkdirAll(cleanupTestDir, 0755); err != nil {
		t.Fatalf("MkdirAll for cleanup test failed: %v", err)
	}
	cleanupCfg := Config{TempDir: cleanupTestDir}
	cleanupUI, err := NewProvisioningUI(ctx, cleanupCfg)
	if err != nil {
		t.Fatalf("NewProvisioningUI for cleanup test failed: %v", err)
	}
	if err := cleanupUI.UpdateLockScreen(ctx, 99, "Cleanup test"); err != nil {
		t.Logf("UpdateLockScreen for cleanup test note: %v", err)
	}
	if err := cleanupUI.Cleanup(ctx); err != nil {
		t.Logf("Cleanup note: %v", err)
	}
	if _, err := os.Stat(cleanupTestDir); !os.IsNotExist(err) {
		t.Errorf("Directory %s still exists after Cleanup, want it to be deleted", cleanupTestDir)
	}
}

func TestUpdateErrorGeneration(t *testing.T) {
	ctx := context.Background()
	outDir := os.Getenv("TEST_UNDECLARED_OUTPUTS_DIR")
	if outDir == "" {
		outDir = t.TempDir()
	}

	errorScreensDir := filepath.Join(outDir, "error_screens")
	if err := os.MkdirAll(errorScreensDir, 0755); err != nil {
		t.Fatalf("MkdirAll failed: %v", err)
	}

	cfg := Config{
		TempDir:         errorScreensDir,
		ErrorTitle:      "Provisioning Error (Step Failed)",
		ErrorFooterText: "Please reboot the machine to retry provisioning",
	}

	ui, err := NewProvisioningUI(ctx, cfg)
	if err != nil {
		t.Fatalf("NewProvisioningUI failed: %v", err)
	}

	errMsg := "Stage stage_2 failed: simulated network timeout"
	if err := ui.UpdateLockScreenError(ctx, 2, errMsg); err != nil {
		t.Logf("UpdateLockScreenError note: %v", err)
	}

	expectedImagePath := filepath.Join(errorScreensDir, "error_step_2.png")
	if _, err := os.Stat(expectedImagePath); os.IsNotExist(err) {
		t.Fatalf("Error image artifact %s not generated, want it to exist", expectedImagePath)
	}

	t.Logf("Successfully generated error image artifact at: %s", expectedImagePath)

	if err := ui.Cleanup(ctx); err != nil {
		t.Logf("Cleanup note: %v", err)
	}

	if _, err := os.Stat(expectedImagePath); os.IsNotExist(err) {
		t.Fatalf("Error image artifact %s was deleted by Cleanup, want it to be preserved", expectedImagePath)
	}

	t.Logf("Error image artifact correctly preserved after Cleanup!")
}
