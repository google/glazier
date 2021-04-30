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

package registry

import (
	"errors"
	"syscall"
	"testing"

	"golang.org/x/sys/windows/registry"
)

const (
	rootKey = `SOFTWARE\TEST\updater`
)

func createKey(path string) error {
	k, _, err := registry.CreateKey(registry.LOCAL_MACHINE, path, registry.ALL_ACCESS)
	if err != nil {
		return err
	}
	defer k.Close()
	return nil
}

func TestSetInteger(t *testing.T) {
	tests := []struct {
		in    int
		inKey string
		err   error
	}{
		{3, "Test1", nil},
		{1, "Test2", nil},
		{0, "Test3", nil},
		{101, "Test4", syscall.Errno(0x02)},
	}
	for _, tt := range tests {
		if tt.err == nil {
			if err := createKey(rootKey); err != nil {
				t.Errorf("createKey(%s) produced unexpected error %v", rootKey, err)
			}
		}
		err := SetInteger(rootKey, tt.inKey, tt.in)
		if !errors.Is(err, tt.err) {
			t.Errorf("SetInteger(%d) returned %v", tt.in, err)
		}
		if err != nil {
			continue
		}
		got, err := GetInteger(rootKey, tt.inKey)
		if err != nil {
			t.Errorf("Verifying SetInteger(%d) returned %v", tt.in, err)
		}
		if int(got) != tt.in {
			t.Errorf("SetInteger(%d) = %d, want %d", tt.in, got, tt.in)
		}
		registry.DeleteKey(registry.LOCAL_MACHINE, rootKey)
	}
}

func TestSetString(t *testing.T) {
	tests := []struct {
		in    string
		inKey string
		err   error
	}{
		{"one", "Test1", nil},
		{"two", "Test2", syscall.Errno(0x02)},
		{"three", "Test3", nil},
	}
	for _, tt := range tests {
		if tt.err == nil {
			if err := createKey(rootKey); err != nil {
				t.Errorf("createKey(%s) produced unexpected error %v", rootKey, err)
			}
		}
		err := SetString(rootKey, tt.inKey, tt.in)
		if !errors.Is(err, tt.err) {
			t.Errorf("SetString(%s) returned %v", tt.in, err)
		}
		if err != nil {
			continue
		}
		got, err := GetString(rootKey, tt.inKey)
		if err != nil {
			t.Errorf("Verifying SetString(%s) returned %v", tt.in, err)
		}
		if got != tt.in {
			t.Errorf("SetString(%s) = %s, want %s", tt.in, got, tt.in)
		}
		registry.DeleteKey(registry.LOCAL_MACHINE, rootKey)
	}
}
