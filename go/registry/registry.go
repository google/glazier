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

// Package registry provides registry interactions for Updater.
package registry

import (
	"fmt"
	"syscall"
	"unsafe"

	reg "golang.org/x/sys/windows/registry"
	"golang.org/x/sys/windows"
)

var (
	modShlwapi = windows.NewLazySystemDLL("shlwapi.dll")

	procSHDeleteKeyW = modShlwapi.NewProc("SHDeleteKeyW")
	// ErrNotExist indicates a registry key did not exist
	ErrNotExist = reg.ErrNotExist
)

// Create a key in the registry.
func Create(path string) error {
	k, _, err := reg.CreateKey(reg.LOCAL_MACHINE, path, reg.ALL_ACCESS)
	if err != nil {
		return err
	}
	defer k.Close()
	return nil
}

// Delete a key from the registry.
func Delete(root, name string) error {
	k, err := reg.OpenKey(reg.LOCAL_MACHINE, root, reg.ALL_ACCESS)
	if err != nil {
		return err
	}
	defer k.Close()
	return k.DeleteValue(name)
}

// DeleteKeyRecursively deletes a key within HKLM and all its subkeys from the registry.
func DeleteKeyRecursively(root, name string) error {
	k, err := reg.OpenKey(reg.LOCAL_MACHINE, root, reg.ALL_ACCESS)
	if err != nil {
		return err
	}
	defer k.Close()
	ret, _, err := procSHDeleteKeyW.Call(uintptr(syscall.Handle(k)), uintptr(unsafe.Pointer(syscall.StringToUTF16Ptr(name))))
	if ret != 0 {
		return fmt.Errorf("DeleteKeyRecursively failure with return code: %d and error: %v", ret, err)
	}
	return nil
}

// GetInteger gets a uint64 value from the registry.
func GetInteger(root, name string) (uint64, error) {
	k, err := reg.OpenKey(reg.LOCAL_MACHINE, root, reg.READ)
	if err != nil {
		return 0, err
	}
	defer k.Close()
	t, _, err := k.GetIntegerValue(name)
	return t, err
}

// GetSubkeys gets all the subkey names under root.
func GetSubkeys(root string) ([]string, error) {
	k, err := reg.OpenKey(reg.LOCAL_MACHINE, root, reg.ENUMERATE_SUB_KEYS)
	if err != nil {
		return []string{}, err
	}
	defer k.Close()
	return k.ReadSubKeyNames(-1)
}

// GetMultiString gets a multi-string key from the registry.
func GetMultiString(root, name string) ([]string, error) {
	k, err := reg.OpenKey(reg.LOCAL_MACHINE, root, reg.READ)
	if err != nil {
		return []string{}, err
	}
	defer k.Close()
	t, _, err := k.GetStringsValue(name)
	return t, err
}

// GetString gets a string key from the registry.
func GetString(root, name string) (string, error) {
	k, err := reg.OpenKey(reg.LOCAL_MACHINE, root, reg.READ)
	if err != nil {
		return "", err
	}
	defer k.Close()
	t, _, err := k.GetStringValue(name)
	return t, err
}

// GetValues gets all the value names under root.
func GetValues(root string) ([]string, error) {
	k, err := reg.OpenKey(reg.LOCAL_MACHINE, root, reg.READ)
	if err != nil {
		return []string{}, err
	}
	defer k.Close()
	return k.ReadValueNames(-1)
}

// SetInteger sets a string key in the registry.
func SetInteger(root, name string, value int) error {
	k, err := reg.OpenKey(reg.LOCAL_MACHINE, root, reg.WRITE)
	if err != nil {
		return err
	}
	defer k.Close()
	return k.SetDWordValue(name, uint32(value))
}

// SetString sets a string key in the registry.
func SetString(root, name, value string) error {
	k, err := reg.OpenKey(reg.LOCAL_MACHINE, root, reg.WRITE)
	if err != nil {
		return err
	}
	defer k.Close()
	return k.SetStringValue(name, value)
}

// SetMultiString sets a multi-string key in the registry.
func SetMultiString(root, name string, value []string) error {
	k, err := reg.OpenKey(reg.LOCAL_MACHINE, root, reg.WRITE)
	if err != nil {
		return err
	}
	defer k.Close()
	return k.SetStringsValue(name, value)
}

// SetBinary sets a binary key in the registry.
func SetBinary(root, name string, value []byte) error {
	k, err := reg.OpenKey(reg.LOCAL_MACHINE, root, reg.WRITE)
	if err != nil {
		return err
	}
	defer k.Close()
	return k.SetBinaryValue(name, value)
}
