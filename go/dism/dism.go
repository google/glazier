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

//go:build generate || windows
// +build generate windows

// Package dism provides an interface to the Deployment Image Servicing and Management (DISM).
//
// Reference: https://docs.microsoft.com/en-us/windows-hardware/manufacture/desktop/dism/deployment-image-servicing-and-management--dism--api
package dism

import (
	"fmt"
	"syscall"
	"unsafe"

	"golang.org/x/sys/windows"
	"github.com/google/logger"
	"github.com/google/glazier/go/helpers"
)

// API Constants
// Ref https://docs.microsoft.com/en-us/windows-hardware/manufacture/desktop/dism/dism-api-constants
const (
	DISM_ONLINE_IMAGE = "DISM_{53BFAE52-B167-4E2F-A258-0A37B57FF845}"

	DISM_MOUNT_READWRITE       = 0x00000000
	DISM_MOUNT_READONLY        = 0x00000001
	DISM_MOUNT_OPTIMIZE        = 0x00000002
	DISM_MOUNT_CHECK_INTEGRITY = 0x00000004

	DISMAPI_S_RELOAD_IMAGE_SESSION_REQUIRED syscall.Errno = 0x00000001
)

// DismPackageIdentifier specifies whether a package is identified by name or by file path.
type DismPackageIdentifier uint32

const (
	// DismPackageNone indicates that no package is specified.
	DismPackageNone DismPackageIdentifier = iota
	// DismPackageName indicates that the package is identified by its name.
	DismPackageName
	// DismPackagePath indicates that the package is specified by its path.
	DismPackagePath
)

// Session holds a dism session. You must call Close() to free up the session upon completion.
type Session struct {
	Handle         *uint32
	imagePath      string
	optWindowsDir  string
	optSystemDrive string
}

// AddCapability adds a Windows capability from an image.
//
// Ref: https://docs.microsoft.com/en-us/windows-hardware/manufacture/desktop/dism/dismaddcapability
func (s Session) AddCapability(
	name string,
	limitAccess bool,
	sourcePaths string,
	sourcePathsCount uint32,
	cancelEvent *windows.Handle,
	progressCallback unsafe.Pointer,
) error {
	var sp **uint16
	if p := helpers.StringToPtrOrNil(sourcePaths); p != nil {
		sp = &p
	}
	return s.checkError(DismAddCapability(*s.Handle, helpers.StringToPtrOrNil(name), limitAccess, sp, sourcePathsCount, cancelEvent, progressCallback, nil))
}

// AddPackage adds Windows packages(s) to an image.
//
// Ref: https://docs.microsoft.com/en-us/windows-hardware/manufacture/desktop/dism/dismaddpackage-function
func (s Session) AddPackage(
	packagePath string,
	ignoreCheck bool,
	preventPending bool,
	cancelEvent *windows.Handle,
	progressCallback unsafe.Pointer,
) error {
	return s.checkError(DismAddPackage(*s.Handle, helpers.StringToPtrOrNil(packagePath), ignoreCheck, preventPending, cancelEvent, progressCallback, nil))
}

// DisableFeature disables Windows Feature(s).
//
// To disable multiple features, separate each feature name with a semicolon.
//
// May return the error windows.ERROR_SUCCESS_REBOOT_REQUIRED if a reboot is required to complete the operation.
//
// Example, disabling a feature:
//   s.DisableFeature("SMB1Protocol", "", nil, nil)
//
// Ref: https://docs.microsoft.com/en-us/windows-hardware/manufacture/desktop/dism/dismdisablefeature-function
func (s Session) DisableFeature(
	feature string,
	optPackageName string,
	cancelEvent *windows.Handle,
	progressCallback unsafe.Pointer,
) error {
	return s.checkError(DismDisableFeature(*s.Handle, helpers.StringToPtrOrNil(feature), helpers.StringToPtrOrNil(optPackageName), false, cancelEvent, progressCallback, nil))
}

// EnableFeature enables Windows Feature(s).
//
// To enable multiple features, separate each feature name with a semicolon.
//
// May return the error windows.ERROR_SUCCESS_REBOOT_REQUIRED if a reboot is required to complete the operation.
//
// Example, enabling a feature, including all dependencies:
//   s.EnableFeature("SMB1Protocol", "", nil, true, nil, nil)
//
// Ref: https://docs.microsoft.com/en-us/windows-hardware/manufacture/desktop/dism/dismenablefeature-function
func (s Session) EnableFeature(
	feature string,
	optIdentifier string,
	optPackageIdentifier *DismPackageIdentifier,
	enableAll bool,
	cancelEvent *windows.Handle,
	progressCallback unsafe.Pointer,
) error {
	return s.checkError(DismEnableFeature(*s.Handle, helpers.StringToPtrOrNil(feature), helpers.StringToPtrOrNil(optIdentifier), optPackageIdentifier, false, nil, 0, enableAll, cancelEvent, progressCallback, nil))
}

// RemoveCapability removes a Windows capability from an image.
//
// Ref: https://docs.microsoft.com/en-us/windows-hardware/manufacture/desktop/dism/dismremovecapability
func (s Session) RemoveCapability(
	name string,
	cancelEvent *windows.Handle,
	progressCallback unsafe.Pointer,
) error {
	return s.checkError(DismRemoveCapability(*s.Handle, helpers.StringToPtrOrNil(name), cancelEvent, progressCallback, nil))
}

// RemovePackage removes Windows packages(s) from an image.
//
// Ref: https://docs.microsoft.com/en-us/windows-hardware/manufacture/desktop/dism/dismremovepackage-function
func (s Session) RemovePackage(
	identifier string,
	packageIdentifier *DismPackageIdentifier,
	cancelEvent *windows.Handle,
	progressCallback unsafe.Pointer,
) error {
	return s.checkError(DismRemovePackage(*s.Handle, helpers.StringToPtrOrNil(identifier), packageIdentifier, cancelEvent, progressCallback, nil))
}

// Close closes the session and shuts down dism. This must be called prior to exiting.
func (s Session) Close() error {
	if err := DismCloseSession(*s.Handle); err != nil {
		return err
	}
	return DismShutdown()
}

// checkError validates the error returned by DISM API and reloads the session if needed
func (s Session) checkError(err error) error {
	if err == DISMAPI_S_RELOAD_IMAGE_SESSION_REQUIRED {
		if err := DismCloseSession(*s.Handle); err != nil {
			logger.Warningf("Closing session before reloading failed: %s", err.Error())
		}

		if err := DismOpenSession(helpers.StringToPtrOrNil(s.imagePath), helpers.StringToPtrOrNil(s.optWindowsDir), helpers.StringToPtrOrNil(s.optSystemDrive), s.Handle); err != nil {
			return fmt.Errorf("reloading session: %w", err)
		}
		logger.Infof("Reloaded image session as requested by DISM API")

		return nil
	}

	return err
}

// DismLogLevel specifies the kind of information that is reported in the log file.
// Ref: https://docs.microsoft.com/en-us/windows-hardware/manufacture/desktop/dism/dismloglevel-enumeration
type DismLogLevel uint32

const (
	// DismLogErrors logs only errors.
	DismLogErrors DismLogLevel = 0
	// DismLogErrorsWarnings logs errors and warnings.
	DismLogErrorsWarnings DismLogLevel = 1
	// DismLogErrorsWarningsInfo logs errors, warnings, and additional information.
	DismLogErrorsWarningsInfo DismLogLevel = 2
)

// OpenSession opens a DISM session. The session can be used for subsequent DISM calls.
//
// Don't forget to call Close() on the returned Session object.
//
// Example, modifying the online image:
//		dism.OpenSession(dism.DISM_ONLINE_IMAGE, "", "", dism.DismLogErrorsWarningsInfo, "", "")
//
// Ref: https://docs.microsoft.com/en-us/windows-hardware/manufacture/desktop/dism/disminitialize-function
// Ref: https://docs.microsoft.com/en-us/windows-hardware/manufacture/desktop/dism/dismopensession-function
func OpenSession(imagePath, optWindowsDir, optSystemDrive string, logLevel DismLogLevel, optLogFilePath, optScratchDir string) (Session, error) {
	var handleVal uint32
	s := Session{
		Handle:         &handleVal,
		imagePath:      imagePath,
		optWindowsDir:  optWindowsDir,
		optSystemDrive: optSystemDrive,
	}

	if err := DismInitialize(logLevel, helpers.StringToPtrOrNil(optLogFilePath), helpers.StringToPtrOrNil(optScratchDir)); err != nil {
		return s, fmt.Errorf("DismInitialize: %w", err)
	}

	if err := DismOpenSession(helpers.StringToPtrOrNil(imagePath), helpers.StringToPtrOrNil(optWindowsDir), helpers.StringToPtrOrNil(optSystemDrive), s.Handle); err != nil {
		return s, fmt.Errorf("DismOpenSession: %w", err)
	}

	return s, nil
}

//go:generate go run golang.org/x/sys/windows/mkwinsyscall -output zdism.go dism.go
//sys DismAddCapability(Session uint32, Name *uint16, LimitAccess bool, SourcePaths **uint16,  SourcePathCount uint32, CancelEvent *windows.Handle, Progress unsafe.Pointer, UserData unsafe.Pointer) (e error) = DismAPI.DismAddCapability
//sys DismAddDriver(Session uint32, DriverPath *uint16, ForceUnsigned bool) (e error) = DismAPI.DismAddDriver
//sys DismAddPackage(Session uint32, PackagePath *uint16, IgnoreCheck bool, PreventPending bool, CancelEvent *windows.Handle, Progress unsafe.Pointer, UserData unsafe.Pointer) (e error) = DismAPI.DismAddPackage
//sys DismApplyUnattend(Session uint32, UnattendFile *uint16, SingleSession bool) (e error) = DismAPI.DismApplyUnattend
//sys DismCloseSession(Session uint32) (e error) = DismAPI.DismCloseSession
//sys DismInitialize(LogLevel DismLogLevel, LogFilePath *uint16, ScratchDirectory *uint16) (e error) = DismAPI.DismInitialize
//sys DismDisableFeature(Session uint32, FeatureName *uint16, PackageName *uint16, RemovePayload bool, CancelEvent *windows.Handle, Progress unsafe.Pointer, UserData unsafe.Pointer) (e error) = DismAPI.DismDisableFeature
//sys DismEnableFeature(Session uint32, FeatureName *uint16, Identifier *uint16, PackageIdentifier *DismPackageIdentifier, LimitAccess bool, SourcePaths *string, SourcePathCount uint32, EnableAll bool, CancelEvent *windows.Handle, Progress unsafe.Pointer, UserData unsafe.Pointer) (e error) = DismAPI.DismEnableFeature
//sys DismOpenSession(ImagePath *uint16, WindowsDirectory *uint16, SystemDrive *uint16, Session *uint32) (e error) = DismAPI.DismOpenSession
//sys DismRemoveCapability(Session uint32, Name *uint16, CancelEvent *windows.Handle, Progress unsafe.Pointer, UserData unsafe.Pointer) (e error) = DismAPI.DismRemoveCapability
//sys DismRemoveDriver(Session uint32, DriverPath *uint16) (e error) = DismAPI.DismRemoveDriver
//sys DismRemovePackage(Session uint32, Identifier *uint16, PackageIdentifier *DismPackageIdentifier, CancelEvent *windows.Handle, Progress unsafe.Pointer, UserData unsafe.Pointer) (e error) = DismAPI.DismRemovePackage
//sys DismShutdown() (e error) = DismAPI.DismShutdown
