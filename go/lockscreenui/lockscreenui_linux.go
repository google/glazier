//go:build !windows

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
	"errors"
	"image"
	"image/color"
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
	TempDir         string
	BaseImagePath   string
	BaseImage       image.Image
	BgColor         color.Color
	TitlePrefix     string
	FooterText      string
	ErrorTitle      string
	ErrorFooterText string
	OverlayPosition Position
}

// ProvisioningUI provides dummy implementations for non-Windows build environments (e.g., Linux wildcard builds).
type ProvisioningUI struct{}

// NewProvisioningUI returns an error on non-Windows platforms.
func NewProvisioningUI(ctx context.Context, cfg Config) (*ProvisioningUI, error) {
	return nil, errors.New("ProvisioningUI is only supported on Windows")
}

// UpdateLockScreen returns an error on non-Windows platforms.
func (ui *ProvisioningUI) UpdateLockScreen(ctx context.Context, step int, message string) error {
	return errors.New("ProvisioningUI is only supported on Windows")
}

// UpdateLockScreenError returns an error on non-Windows platforms.
func (ui *ProvisioningUI) UpdateLockScreenError(ctx context.Context, step int, errorMessage string) error {
	return errors.New("ProvisioningUI is only supported on Windows")
}

// Cleanup returns nil on non-Windows platforms.
func (ui *ProvisioningUI) Cleanup(ctx context.Context) error {
	return nil
}
