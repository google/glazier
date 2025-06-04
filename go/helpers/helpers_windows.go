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

//go:build windows
// +build windows

package helpers

import (
	"fmt"
	"regexp"
	"syscall"
	"time"
	"unsafe"

	"github.com/google/deck"
	"golang.org/x/sys/windows/registry"
	"golang.org/x/sys/windows/svc/mgr"
	"golang.org/x/sys/windows/svc"
	"golang.org/x/sys/windows"
	"github.com/iamacarpet/go-win64api"
)

var (
	moduser32            = windows.NewLazySystemDLL("user32.dll")
	modkernel32          = windows.NewLazySystemDLL("kernel32.dll")
	prodGetSystemMetrics = moduser32.NewProc("GetSystemMetrics")
	prodSetWindowPos     = moduser32.NewProc("SetWindowPos")
	prodGetConsoleWindow = modkernel32.NewProc("GetConsoleWindow")
)

var (
	// Test helpers
	fnProcessList = winapi.ProcessList
)

const (
	// https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getsystemmetrics
	smCxScreen = 0
	smCyScreen = 1
	// https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setwindowpos
	swpNoZOrder   = 0x0004
	swpShowWindow = 0x0040
)

// GetServiceState interrogates local system services and returns their status and configuration.
func GetServiceState(name string) (svc.Status, mgr.Config, error) {
	m, err := mgr.Connect()
	if err != nil {
		return svc.Status{}, mgr.Config{}, err
	}
	defer m.Disconnect()
	s, err := m.OpenService(name)
	if err != nil {
		return svc.Status{}, mgr.Config{}, fmt.Errorf("could not access service: %v", err)
	}
	defer s.Close()

	config, err := s.Config()
	if err != nil {
		return svc.Status{}, mgr.Config{}, err
	}
	status, err := s.Query()
	return status, config, err
}

// ChangeService can change a services type or/and startup behaviour
// https://docs.microsoft.com/en-us/dotnet/api/system.serviceprocess.servicestartmode
// https://docs.microsoft.com/en-us/dotnet/api/system.serviceprocess.servicetype
func ChangeService(name string, c mgr.Config) error {
	m, err := mgr.Connect()
	if err != nil {
		return err
	}
	defer m.Disconnect()
	s, err := m.OpenService(name)
	if err != nil {
		return fmt.Errorf("could not access service: %v", err)
	}
	defer s.Close()

	return s.UpdateConfig(c)
}

const (
	HWND_BROADCAST   = uintptr(0xffff)
	WM_SETTINGCHANGE = uintptr(0x001A)
)

// GetSysEnv gets a system environment variable
func GetSysEnv(key string) (string, error) {
	k, err := registry.OpenKey(registry.LOCAL_MACHINE, `System\CurrentControlSet\Control\Session Manager\Environment`, registry.READ)
	if err != nil {
		return "", err
	}
	defer k.Close()
	v, _, err := k.GetStringValue(key)
	return v, err
}

// RestartService attempts to restart local system services.
func RestartService(name string) error {
	m, err := mgr.Connect()
	if err != nil {
		return err
	}
	defer m.Disconnect()
	s, err := m.OpenService(name)
	if err != nil {
		return err
	}
	defer s.Close()

	if err := stopService(s); err != nil {
		return err
	}

	return s.Start()
}

// RestartServiceWithVerify attempts to restart local system services and verifies the service is running with a 60 second timeout.
func RestartServiceWithVerify(name string, retryCount ...int) error {
	retryAttempts := 12
	if len(retryCount) > 0 {
		retryAttempts = retryCount[0]
	}
	if err := RestartService(name); err != nil {
		return err
	}
	status := svc.Status{
		State: svc.StartPending, // Assume the service is starting
	}
	for retry := 0; status.State == svc.StartPending; retry++ {
		deck.Infof("Waiting for service %q to start, sleeping for 5 seconds", name)
		time.Sleep(5 * time.Second)
		var err error
		status, _, err = GetServiceState(name)
		if err != nil {
			return err
		}
		if retry == retryAttempts {
			return fmt.Errorf("timed out waiting for service %q to start", name)
		}
	}
	if status.State != svc.Running {
		return fmt.Errorf("service %q is not running after restart, current state: %v", name, status.State)
	}
	return nil
}

// SetSysEnv sets a system environment variable
func SetSysEnv(key, value string) error {
	k, err := registry.OpenKey(registry.LOCAL_MACHINE, `System\CurrentControlSet\Control\Session Manager\Environment`, registry.SET_VALUE)
	if err != nil {
		return err
	}
	defer k.Close()
	if err := k.SetStringValue(key, value); err != nil {
		return err
	}

	// refresh existing windows
	r, _, err := syscall.NewLazyDLL("user32.dll").NewProc("SendMessageW").Call(HWND_BROADCAST, WM_SETTINGCHANGE, 0, uintptr(unsafe.Pointer(syscall.StringToUTF16Ptr("ENVIRONMENT"))))
	if r != 1 {
		return fmt.Errorf("SendMessageW() exited with %q and error %v", r, err)
	}
	return nil
}

// StartService attempts to start local system services.
func StartService(name string) error {
	m, err := mgr.Connect()
	if err != nil {
		return err
	}
	defer m.Disconnect()
	s, err := m.OpenService(name)
	if err != nil {
		return err
	}
	defer s.Close()

	return s.Start()
}

// StartServiceWithVerify attempts to start local system services and verifies
// the service is running. Will retry every 5 seconds, with a default of a 60 second timeout.
func StartServiceWithVerify(name string, retryCount ...int) error {
	retryAttempts := 12
	if len(retryCount) > 0 {
		retryAttempts = retryCount[0]
	}
	if err := StartService(name); err != nil {
		return err
	}
	status := svc.Status{
		State: svc.StartPending, // Assume the service is starting
	}
	for retry := 0; status.State == svc.StartPending; retry++ {
		deck.Infof("Waiting for service %q to start, sleeping for 5 seconds", name)
		time.Sleep(5 * time.Second)
		var err error
		status, _, err = GetServiceState(name)
		if err != nil {
			return err
		}
		if retry == retryAttempts {
			return fmt.Errorf("timed out waiting for service %q to start", name)
		}
	}
	if status.State != svc.Running {
		return fmt.Errorf("service %q is not running after start, current state: %v", name, status.State)
	}
	return nil
}

func stopService(s *mgr.Service) error {
	// although s.Control returns stat, if the service is already stopped it returns an error
	stat, err := s.Query()
	if err != nil {
		return err
	}
	if stat.State == svc.Stopped {
		return nil
	}
	stat, err = s.Control(svc.Stop)
	if err != nil {
		return err
	}
	retry := 0
	for stat.State != svc.Stopped {
		deck.Infof("Waiting for service %q to stop.", s.Name)
		time.Sleep(5 * time.Second)
		retry++
		if retry > 12 {
			return fmt.Errorf("timed out waiting for service %q to stop", s.Name)
		}
		stat, err = s.Query()
		if err != nil {
			return err
		}
	}
	return nil
}

// StopService attempts to stop local system services.
func StopService(name string) error {
	m, err := mgr.Connect()
	if err != nil {
		return err
	}
	defer m.Disconnect()
	s, err := m.OpenService(name)
	if err != nil {
		return err
	}
	defer s.Close()

	return stopService(s)
}

// WaitForProcessExit waits for a process to stop (no longer appear in the process list).
func WaitForProcessExit(matcher *regexp.Regexp, timeout time.Duration) error {
	t := time.NewTicker(timeout)
	defer t.Stop()
	r := time.NewTicker(5 * time.Second)
	defer r.Stop()

loop:
	for {
		select {
		case <-t.C:
			return ErrTimeout
		case <-r.C:
			procs, err := fnProcessList()
			if err != nil {
				return fmt.Errorf("winapi.ProcessList: %w", err)
			}
			for _, p := range procs {
				if matcher.MatchString(p.Executable) {
					deck.Warningf("Process %s still running; waiting for exit.", p.Executable)
					goto loop
				}
			}
			return nil
		}
	}
}

// StringToPtrOrNil converts a non-empty string to a UTF16Ptr, but leaves a nil value for empty strings.
//
// This is primarily useful for Windows API calls where an "unset" parameter must be nil, and a pointer to
// an empty string would be considered invalid.
func StringToPtrOrNil(in string) (out *uint16) {
	if in != "" {
		out = windows.StringToUTF16Ptr(in)
	}
	return
}

// SetConsoleRight sets the console window position to the right side of the screen.
// If width or height is 0, sane defaults are used.
func SetConsoleRight(width, height int) error {
	// Get console window handle.
	hwnd, _, err := prodGetConsoleWindow.Call()
	if hwnd == 0 {
		return fmt.Errorf("GetConsoleWindow failed: %w", err)
	}
	// Get screen width and height.
	screenWidth, _, err := prodGetSystemMetrics.Call(smCxScreen)
	if screenWidth == 0 {
		return fmt.Errorf("GetSystemMetrics failed: %w", err)
	}
	screenHeight, _, err := prodGetSystemMetrics.Call(smCyScreen)
	if screenHeight == 0 {
		return fmt.Errorf("GetSystemMetrics failed: %w", err)
	}
	// Make sure to not cover taskbar.
	if height == 0 {
		height = int(screenHeight) - 100
	}
	if width == 0 {
		width = 500
	}
	// Calculate the top-right position.
	x := screenWidth - uintptr(width)
	// Move window to top right corner.
	// https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setwindowpos
	returnCode, _, err := prodSetWindowPos.Call(hwnd, 0, uintptr(x), 0, uintptr(width), uintptr(height), swpNoZOrder|swpShowWindow)
	if returnCode == 0 {
		return fmt.Errorf("prodSetWindowPos failed: %w", err)
	}
	return nil
}
