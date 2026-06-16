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

// Package lockscreenui provides a robust, reusable UI manager for displaying provisioning and configuration progress
// on the Windows lock screen.
package lockscreenui

import (
	"golang.org/x/net/context"
	"fmt"
	"image"
	"image/color"
	"math"
	"os"
	"path/filepath"

	"github.com/google/deck"
	"github.com/fogleman/gg"
	"github.com/google/glazier/go/helpers"
	"github.com/google/glazier/go/registry"

	_ "image/jpeg" // Required for decoding JPEG background images
	_ "image/png"  // Required for decoding PNG background images
)

const (
	registryPolicyKey = `SOFTWARE\Policies\Microsoft\Windows\Personalization`
	registryValueName = "LockScreenImage"
)

var (
	fontPath = filepath.Join(os.Getenv("windir"), "Fonts", "segoeui.ttf") // Native to modern Windows
)

// Position defines where the progress overlay box is positioned on the screen.
type Position string

const (
	// PositionCenter positions the overlay in the center of the screen.
	PositionCenter Position = "center"
	// PositionTop positions the overlay in the top portion of the screen.
	PositionTop Position = "top"
	// PositionBottom positions the overlay in the bottom portion of the screen.
	PositionBottom Position = "bottom"
)

// Config defines the configuration for the ProvisioningUI manager.
type Config struct {
	// TempDir is the directory where generated lock screen images are temporarily stored.
	TempDir string
	// BaseImagePath is the optional path to a background image (JPEG or PNG).
	BaseImagePath string
	// BaseImage is an optional pre-loaded background image.
	BaseImage image.Image
	// BgColor is the background color used if no base image is provided. Defaults to solid Windows Blue (0, 120, 215).
	BgColor color.Color
	// TitlePrefix is the prefix for progress messages (e.g., "Provisioning: ").
	TitlePrefix string
	// FooterText is the footer displayed on progress screens.
	FooterText string
	// ErrorTitle is the title displayed on error screens.
	ErrorTitle string
	// ErrorFooterText is the footer displayed on error screens.
	ErrorFooterText string
	// OverlayPosition defines the vertical placement of the progress box on the screen. Defaults to PositionCenter.
	OverlayPosition Position
}

// ProvisioningUI manages the state of the lock screen updates.
type ProvisioningUI struct {
	cfg           Config
	lastImagePath string // Tracks the previous step's image so we can delete it
	hasError      bool   // If true, Cleanup preserves the error screen and policy so the user can see the failure notification
}

// NewProvisioningUI initializes the UI manager with the provided configuration.
func NewProvisioningUI(ctx context.Context, cfg Config) (*ProvisioningUI, error) {
	deck.Infof("Initializing ProvisioningUI manager (tempDir: %q)", cfg.TempDir)

	if cfg.TempDir == "" {
		return nil, fmt.Errorf("TempDir cannot be empty")
	}

	// Set sensible defaults if not provided
	if cfg.BgColor == nil {
		cfg.BgColor = color.RGBA{0, 120, 215, 255} // Default Windows Blue
	}
	if cfg.TitlePrefix == "" {
		cfg.TitlePrefix = "Progress: "
	}
	if cfg.ErrorTitle == "" {
		cfg.ErrorTitle = "Error (Step Failed)"
	}
	if cfg.OverlayPosition == "" {
		cfg.OverlayPosition = PositionCenter
	}

	if cfg.BaseImagePath != "" {
		deck.Infof("Validating custom base image path: %s", cfg.BaseImagePath)
		if _, err := os.Stat(cfg.BaseImagePath); os.IsNotExist(err) {
			deck.Errorf("Base image not found at %s: %v", cfg.BaseImagePath, err)
			return nil, fmt.Errorf("base image not found at %s: %w", cfg.BaseImagePath, err)
		}
	}

	deck.Infof("Ensuring temporary output directory exists: %s", cfg.TempDir)
	if err := os.MkdirAll(cfg.TempDir, 0755); err != nil {
		deck.Errorf("Failed to create temp directory %s: %v", cfg.TempDir, err)
		return nil, fmt.Errorf("failed to create temp directory: %w", err)
	}

	return &ProvisioningUI{
		cfg: cfg,
	}, nil
}

// UpdateLockScreen renders the new frame, applies it, and refreshes the screen.
func (ui *ProvisioningUI) UpdateLockScreen(ctx context.Context, step int, message string) error {
	outputPath := filepath.Join(ui.cfg.TempDir, fmt.Sprintf("step_%d.png", step))
	deck.Infof("Updating lock screen progress (step: %d, output: %q)", step, outputPath)

	if err := ui.renderWallpaper(message, outputPath); err != nil {
		deck.Errorf("Failed to render progress wallpaper for step %d: %v", step, err)
		return fmt.Errorf("failed to render frame for step %d: %w", step, err)
	}

	if err := ui.setRegistryPolicy(outputPath); err != nil {
		deck.Errorf("Failed to set LockScreenImage registry policy: %v", err)
		return fmt.Errorf("failed to set registry policy: %w", err)
	}

	ui.forceScreenRefresh()

	if ui.lastImagePath != "" && ui.lastImagePath != outputPath {
		deck.Infof("Cleaning up previous progress image: %s", ui.lastImagePath)
		_ = os.Remove(ui.lastImagePath)
	}
	ui.lastImagePath = outputPath

	return nil
}

// UpdateLockScreenError renders a distinct dark red failure notification screen, applies it, and preserves it.
func (ui *ProvisioningUI) UpdateLockScreenError(ctx context.Context, step int, errorMessage string) error {
	deck.Warningf("Provisioning failure detected at step %d. Generating alert lock screen.", step)
	ui.hasError = true

	outputPath := filepath.Join(ui.cfg.TempDir, fmt.Sprintf("error_step_%d.png", step))

	if err := ui.renderErrorWallpaper(errorMessage, outputPath); err != nil {
		deck.Errorf("Failed to render error wallpaper for step %d: %v", step, err)
		return fmt.Errorf("failed to render error frame for step %d: %w", step, err)
	}

	if err := ui.setRegistryPolicy(outputPath); err != nil {
		deck.Errorf("Failed to set error LockScreenImage registry policy: %v", err)
		return fmt.Errorf("failed to set error registry policy: %w", err)
	}

	ui.forceScreenRefresh()

	if ui.lastImagePath != "" && ui.lastImagePath != outputPath {
		deck.Infof("Cleaning up previous image before displaying error: %s", ui.lastImagePath)
		_ = os.Remove(ui.lastImagePath)
	}
	ui.lastImagePath = outputPath

	return nil
}

// ForceCleanup unconditionally removes policies and temp files, restoring the system to normal regardless of error state.
func (ui *ProvisioningUI) ForceCleanup(ctx context.Context) error {
	ui.hasError = false
	return ui.Cleanup(ctx)
}

// Cleanup removes policies and temp files, restoring the system to normal.
func (ui *ProvisioningUI) Cleanup(ctx context.Context) error {
	if ui.hasError {
		deck.Warning("Provisioning finished with an error. Preserving error wallpaper and Group Policy intact.")
		return nil
	}

	deck.Info("Provisioning completed successfully. Initiating UI footprint cleanup.")
	var cleanupErrors []error

	deck.Infof("Removing Group Policy registry value: %s\\%s", registryPolicyKey, registryValueName)
	if err := registry.Delete(registryPolicyKey, registryValueName); err != nil && err != registry.ErrNotExist {
		deck.Warningf("Failed to delete registry value: %v", err)
		cleanupErrors = append(cleanupErrors, fmt.Errorf("failed to delete registry value: %w", err))
	}

	deck.Infof("Removing temporary screens directory: %s", ui.cfg.TempDir)
	if err := os.RemoveAll(ui.cfg.TempDir); err != nil {
		deck.Warningf("Failed to remove temp directory %s: %v", ui.cfg.TempDir, err)
		cleanupErrors = append(cleanupErrors, fmt.Errorf("failed to remove temp directory: %w", err))
	}

	deck.Info("Triggering final logon screen refresh to restore default Windows wallpaper.")
	ui.forceScreenRefresh()

	if len(cleanupErrors) > 0 {
		return fmt.Errorf("cleanup finished with errors: %v", cleanupErrors)
	}
	return nil
}

// --- Internal Helper Methods ---

func (ui *ProvisioningUI) renderWallpaper(text, outputPath string) error {
	var bgImage image.Image
	var err error

	if ui.cfg.BaseImage != nil {
		bgImage = ui.cfg.BaseImage
	} else if ui.cfg.BaseImagePath != "" {
		bgImage, err = gg.LoadImage(ui.cfg.BaseImagePath)
		if err != nil {
			return fmt.Errorf("could not load base image: %w", err)
		}
	}

	var width, height int
	var dc *gg.Context

	if bgImage != nil {
		bounds := bgImage.Bounds()
		width = bounds.Dx()
		height = bounds.Dy()
		dc = gg.NewContext(width, height)
		dc.DrawImage(bgImage, 0, 0)
	} else {
		// Default 1080p canvas with solid background color
		width = 1920
		height = 1080
		dc = gg.NewContext(width, height)
		dc.SetColor(ui.cfg.BgColor)
		dc.Clear()
	}

	if err := dc.LoadFontFace(fontPath, 48); err != nil {
		return fmt.Errorf("could not load font %s: %w", fontPath, err)
	}
	fullText := fmt.Sprintf("%s%s", ui.cfg.TitlePrefix, text)
	titleWidth, titleHeight := dc.MeasureString(fullText)

	var footerWidth, footerHeight float64
	if ui.cfg.FooterText != "" {
		if err := dc.LoadFontFace(fontPath, 32); err != nil {
			return fmt.Errorf("could not load font %s: %w", fontPath, err)
		}
		footerWidth, footerHeight = dc.MeasureString(ui.cfg.FooterText)
	}

	padding := 40.0
	lineSpacing := 20.0
	boxWidth := math.Max(titleWidth, footerWidth) + (padding * 2)
	boxHeight := titleHeight + (padding * 2)
	if ui.cfg.FooterText != "" {
		boxHeight += footerHeight + lineSpacing
	}
	boxX := (float64(width) - boxWidth) / 2.0

	var boxY float64
	switch ui.cfg.OverlayPosition {
	case PositionTop:
		boxY = float64(height) * 0.15
	case PositionBottom:
		boxY = float64(height)*0.80 - boxHeight
	default: // PositionCenter
		boxY = (float64(height) - boxHeight) / 2.0
	}

	dc.DrawRoundedRectangle(boxX, boxY, boxWidth, boxHeight, 15) // 15px border radius
	dc.SetRGBA(0, 0, 0, 0.75)                                    // 75% opaque black for excellent contrast
	dc.Fill()

	if err := dc.LoadFontFace(fontPath, 48); err != nil {
		return fmt.Errorf("could not reload font %s: %w", fontPath, err)
	}
	dc.SetRGB(1, 1, 1) // Crisp white text
	boxCenterY := boxY + (boxHeight / 2.0)
	totalTextHeight := titleHeight
	if ui.cfg.FooterText != "" {
		totalTextHeight += lineSpacing + footerHeight
	}
	startY := boxCenterY - (totalTextHeight / 2.0)
	titleY := startY + (titleHeight / 2.0)
	dc.DrawStringAnchored(fullText, float64(width)/2.0, titleY, 0.5, 0.5)

	if ui.cfg.FooterText != "" {
		if err := dc.LoadFontFace(fontPath, 32); err != nil {
			return fmt.Errorf("could not reload font %s: %w", fontPath, err)
		}
		dc.SetRGB(0.85, 0.85, 0.85)
		footerY := startY + titleHeight + lineSpacing + (footerHeight / 2.0)
		dc.DrawStringAnchored(ui.cfg.FooterText, float64(width)/2.0, footerY, 0.5, 0.5)
	}

	// Ensure the output directory exists, as it might have been removed by a prior Cleanup.
	if err := os.MkdirAll(filepath.Dir(outputPath), 0755); err != nil {
		return fmt.Errorf("failed to create output directory %s: %w", filepath.Dir(outputPath), err)
	}

	if err := dc.SavePNG(outputPath); err != nil {
		return fmt.Errorf("failed to save generated PNG: %w", err)
	}

	return nil
}

func (ui *ProvisioningUI) renderErrorWallpaper(errorMessage, outputPath string) error {
	var bgImage image.Image
	var err error

	if ui.cfg.BaseImage != nil {
		bgImage = ui.cfg.BaseImage
	} else if ui.cfg.BaseImagePath != "" {
		bgImage, err = gg.LoadImage(ui.cfg.BaseImagePath)
		if err != nil {
			return fmt.Errorf("could not load base image: %w", err)
		}
	}

	var width, height int
	var dc *gg.Context

	if bgImage != nil {
		bounds := bgImage.Bounds()
		width = bounds.Dx()
		height = bounds.Dy()
		dc = gg.NewContext(width, height)
		dc.DrawImage(bgImage, 0, 0)
	} else {
		width = 1920
		height = 1080
		dc = gg.NewContext(width, height)
		dc.SetColor(ui.cfg.BgColor)
		dc.Clear()
	}

	if err := dc.LoadFontFace(fontPath, 48); err != nil {
		return fmt.Errorf("could not load font %s: %w", fontPath, err)
	}
	titleWidth, titleHeight := dc.MeasureString(ui.cfg.ErrorTitle)

	if err := dc.LoadFontFace(fontPath, 32); err != nil {
		return fmt.Errorf("could not load font %s: %w", fontPath, err)
	}
	msgWidth, msgHeight := dc.MeasureString(errorMessage)

	var footerWidth, footerHeight float64
	if ui.cfg.ErrorFooterText != "" {
		footerWidth, footerHeight = dc.MeasureString(ui.cfg.ErrorFooterText)
	}

	padding := 40.0
	lineSpacing := 20.0
	maxTextWidth := math.Max(titleWidth, math.Max(msgWidth, footerWidth))
	boxWidth := maxTextWidth + (padding * 2)
	boxHeight := titleHeight + msgHeight + (lineSpacing * 2) + (padding * 2)
	if ui.cfg.ErrorFooterText != "" {
		boxHeight += footerHeight + lineSpacing
	}
	boxX := (float64(width) - boxWidth) / 2.0

	var boxY float64
	switch ui.cfg.OverlayPosition {
	case PositionTop:
		boxY = float64(height) * 0.15
	case PositionBottom:
		boxY = float64(height)*0.80 - boxHeight
	default: // PositionCenter
		boxY = (float64(height) - boxHeight) / 2.0
	}

	dc.DrawRoundedRectangle(boxX, boxY, boxWidth, boxHeight, 15)
	dc.SetRGBA(0.65, 0.0, 0.0, 0.85) // 85% opaque dark red alert box
	dc.Fill()

	if err := dc.LoadFontFace(fontPath, 48); err != nil {
		return fmt.Errorf("could not reload font %s: %w", fontPath, err)
	}
	dc.SetRGB(1, 1, 1)
	boxCenterY := boxY + (boxHeight / 2.0)
	totalTextHeight := titleHeight + msgHeight + lineSpacing
	if ui.cfg.ErrorFooterText != "" {
		totalTextHeight += lineSpacing + footerHeight
	}
	startY := boxCenterY - (totalTextHeight / 2.0)
	titleY := startY + (titleHeight / 2.0)
	dc.DrawStringAnchored(ui.cfg.ErrorTitle, float64(width)/2.0, titleY, 0.5, 0.5)

	if err := dc.LoadFontFace(fontPath, 32); err != nil {
		return fmt.Errorf("could not reload font %s: %w", fontPath, err)
	}
	dc.SetRGB(1, 0.95, 0.2) // Bright yellow for the failure message to prioritize readability
	msgY := startY + titleHeight + lineSpacing + (msgHeight / 2.0)
	dc.DrawStringAnchored(errorMessage, float64(width)/2.0, msgY, 0.5, 0.5)

	if ui.cfg.ErrorFooterText != "" {
		dc.SetRGB(0.9, 0.9, 0.9)
		footerY := startY + titleHeight + msgHeight + (lineSpacing * 2) + (footerHeight / 2.0)
		dc.DrawStringAnchored(ui.cfg.ErrorFooterText, float64(width)/2.0, footerY, 0.5, 0.5)
	}

	if err := dc.SavePNG(outputPath); err != nil {
		return fmt.Errorf("failed to save generated error PNG: %w", err)
	}

	return nil
}

func (ui *ProvisioningUI) setRegistryPolicy(imagePath string) error {
	deck.Infof("Ensuring registry policy key exists: %s", registryPolicyKey)
	_ = registry.Create(registryPolicyKey)

	deck.Infof("Setting registry value %s\\%s = %s", registryPolicyKey, registryValueName, imagePath)
	if err := registry.SetString(registryPolicyKey, registryValueName, imagePath); err != nil {
		return fmt.Errorf("failed to set registry value: %w", err)
	}

	return nil
}

func (ui *ProvisioningUI) forceScreenRefresh() {
	deck.Info("Executing taskkill on LogonUI.exe to force lock screen redraw")
	_, _ = helpers.Exec("taskkill", []string{"/F", "/IM", "LogonUI.exe"}, nil)
}
