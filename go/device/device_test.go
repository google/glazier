//go:build windows

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

package device

import (
	"errors"
	"fmt"
	"io/ioutil"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/google/go-cmp/cmp"
	reg "golang.org/x/sys/windows/registry"
)

func TestChassisType(t *testing.T) {
	origGetChassisType := getChassisType
	defer func() { getChassisType = origGetChassisType }()

	tests := []struct {
		name    string
		mock    Type
		mockErr error
		want    Type
		wantErr bool
	}{
		{
			name: "Desktop",
			mock: Desktop,
			want: Desktop,
		},
		{
			name: "Laptop",
			mock: Laptop,
			want: Laptop,
		},
		{
			name: "Other",
			mock: Other,
			want: Other,
		},
		{
			name: "Unknown",
			mock: Unknown,
			want: Unknown,
		},
		{
			name:    "Error",
			mock:    Unknown,
			mockErr: errors.New("failed to read SMBIOS"),
			want:    Unknown,
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			getChassisType = func() (Type, error) {
				return tt.mock, tt.mockErr
			}
			got, err := ChassisType()
			if (err != nil) != tt.wantErr {
				t.Fatalf("ChassisType() error = %v, wantErr = %v", err, tt.wantErr)
			}
			if got != tt.want {
				t.Errorf("ChassisType() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestGetDomainRole(t *testing.T) {
	origRegistryGetString := registryGetString
	defer func() { registryGetString = origRegistryGetString }()

	tests := []struct {
		name      string
		mockValue string
		mockErr   error
		want      DomainRole
		wantErr   bool
	}{
		{
			name:      "Workstation",
			mockValue: "WinNT",
			want:      Workstation,
		},
		{
			name:      "Server",
			mockValue: "ServerNT",
			want:      Server,
		},
		{
			name:      "DomainController",
			mockValue: "LanmanNT",
			want:      DomainController,
		},
		{
			name:      "UnknownRole",
			mockValue: "Other",
			want:      RoleUnknown,
		},
		{
			name:    "RegistryError",
			mockErr: errors.New("registry read failed"),
			want:    RoleUnknown,
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			registryGetString = func(path, name string) (string, error) {
				if path != `SYSTEM\CurrentControlSet\Control\ProductOptions` || name != "ProductType" {
					return "", fmt.Errorf("unexpected registry query: path=%q, name=%q", path, name)
				}
				return tt.mockValue, tt.mockErr
			}

			got, err := GetDomainRole()
			if (err != nil) != tt.wantErr {
				t.Fatalf("GetDomainRole() error = %v, wantErr = %v", err, tt.wantErr)
			}
			if got != tt.want {
				t.Errorf("GetDomainRole() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestGetDomainJoined(t *testing.T) {
	origNetGetJoinInformation := netGetJoinInformation
	origNetAPIBufferFree := netAPIBufferFree
	defer func() {
		netGetJoinInformation = origNetGetJoinInformation
		netAPIBufferFree = origNetAPIBufferFree
	}()

	tests := []struct {
		name           string
		mockErr        error
		joinStatus     uint32
		mockDomainName bool
		want           bool
		wantErr        bool
	}{
		{
			name:           "DomainJoined",
			joinStatus:     3, // NetSetupDomainName.
			mockDomainName: true,
			want:           true,
		},
		{
			name:           "NotDomainJoined",
			joinStatus:     1, // NetSetupUnjoined
			mockDomainName: true,
			want:           false,
		},
		{
			name:    "APIFailure",
			mockErr: errors.New("ERROR_NO_SUCH_DOMAIN"),
			want:    false,
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			bufferFreed := false
			netGetJoinInformation = func(server *uint16, name **uint16, bufType *uint32) error {
				if tt.mockErr != nil {
					return tt.mockErr
				}
				if name != nil && tt.mockDomainName {
					var dummy uint16 = 'D'
					*name = &dummy
				}
				if bufType != nil {
					*bufType = tt.joinStatus
				}
				return nil
			}
			netAPIBufferFree = func(buf *byte) error {
				bufferFreed = true
				return nil
			}

			got, err := GetDomainJoined()
			if (err != nil) != tt.wantErr {
				t.Fatalf("GetDomainJoined() error = %v, wantErr = %v", err, tt.wantErr)
			}
			if got != tt.want {
				t.Errorf("GetDomainJoined() = %v, want %v", got, tt.want)
			}
			if tt.mockDomainName && !bufferFreed {
				t.Errorf("GetDomainJoined() did not free domain name buffer")
			}
		})
	}
}

func TestModel(t *testing.T) {
	origRegistryGetString := registryGetString
	defer func() { registryGetString = origRegistryGetString }()

	tests := []struct {
		name            string
		isLive          bool
		manufacturer    string
		manufacturerErr error
		family          string
		familyErr       error
		productName     string
		productNameErr  error
		want            string
		wantErr         bool
	}{
		{
			name:   "Live_VM",
			isLive: true,
		},
		{
			name:         "NonLenovo",
			manufacturer: "Dell Inc.",
			productName:  "Precision 5530",
			want:         "Precision 5530",
		},
		{
			name:         "Lenovo",
			manufacturer: "LENOVO",
			family:       "ThinkPad P1 Gen 4",
			want:         "ThinkPad P1 Gen 4",
		},
		{
			name:            "ManufacturerError",
			manufacturerErr: errors.New("registry read error"),
			want:            "unknown",
			wantErr:         true,
		},
		{
			name:           "NonLenovoProductNameError",
			manufacturer:   "Dell Inc.",
			productNameErr: errors.New("product name missing"),
			want:           "unknown",
			wantErr:        true,
		},
		{
			name:         "LenovoFamilyError",
			manufacturer: "Lenovo",
			familyErr:    errors.New("family missing"),
			want:         "unknown",
			wantErr:      true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if tt.isLive {
				registryGetString = origRegistryGetString
				got, err := Model()
				if err != nil {
					t.Fatalf("Model() error = %v, wantErr = %v", err, tt.wantErr)
				}
				if got == "" || got == "unknown" {
					t.Errorf("Model() live returned %q, want valid model name", got)
				}
				t.Logf("Model() on live system = %q", got)
				return
			}

			registryGetString = func(path, name string) (string, error) {
				if path != `HARDWARE\DESCRIPTION\System\BIOS` {
					return "", fmt.Errorf("unexpected registry path %q", path)
				}
				switch name {
				case "SystemManufacturer":
					return tt.manufacturer, tt.manufacturerErr
				case "SystemFamily":
					return tt.family, tt.familyErr
				case "SystemProductName":
					return tt.productName, tt.productNameErr
				default:
					return "", fmt.Errorf("unexpected registry value name %q", name)
				}
			}

			got, err := Model()
			if (err != nil) != tt.wantErr {
				t.Fatalf("Model() error = %v, wantErr = %v", err, tt.wantErr)
			}
			if got != tt.want {
				t.Errorf("Model() = %q, want %q", got, tt.want)
			}
		})
	}
}

func TestHardwareModel(t *testing.T) {
	origRegistryGetString := registryGetString
	defer func() { registryGetString = origRegistryGetString }()

	tests := []struct {
		name             string
		isLive           bool
		mockModel        string
		mockManufacturer string
		mockModelErr     error
		mockMfgErr       error
		wantModel        string
		wantErr          bool
	}{
		{
			name:   "Live_VM",
			isLive: true,
		},
		{
			name:             "Lenovo_X1_2in1_Gen10",
			mockModel:        "21NVS12300",
			mockManufacturer: "LENOVO",
			wantModel:        "21nv",
		},
		{
			name:             "Lenovo_X1_Carbon_Gen12",
			mockModel:        "21KDS15P00",
			mockManufacturer: "Lenovo",
			wantModel:        "21kd",
		},
		{
			name:             "Lenovo_Short_Model",
			mockModel:        "X1",
			mockManufacturer: "LENOVO",
			wantModel:        "x1",
		},
		{
			name:             "Dell_Precision",
			mockModel:        "Precision 5570",
			mockManufacturer: "Dell Inc.",
			wantModel:        "precision 5570",
		},
		{
			name:             "HP_ZBook",
			mockModel:        "HP ZBook Studio G8",
			mockManufacturer: "HP",
			wantModel:        "hp zbook studio g8",
		},
		{
			name:             "Google_VM",
			mockModel:        "Google Compute Engine",
			mockManufacturer: "Google",
			wantModel:        "google compute engine",
		},
		{
			name:             "Whitespace_Trimming_And_Lowercase",
			mockModel:        "  21NVS12300  ",
			mockManufacturer: "  LENOVO  ",
			wantModel:        "21nv",
		},
		{
			name:             "Empty_Model",
			mockModel:        "   ",
			mockManufacturer: "LENOVO",
			wantModel:        "",
		},
		{
			name:         "Missing_Model_Registry_Key",
			mockModelErr: reg.ErrNotExist,
			wantModel:    "",
		},
		{
			name:         "Model_Registry_Error",
			mockModelErr: errors.New("access denied"),
			wantErr:      true,
		},
		{
			name:             "Missing_Manufacturer_Registry_Key",
			mockModel:        "Precision 5570",
			mockMfgErr:       reg.ErrNotExist,
			wantModel:        "precision 5570",
		},
		{
			name:             "Manufacturer_Registry_Error",
			mockModel:        "Precision 5570",
			mockMfgErr:       errors.New("access denied"),
			wantErr:          true,
		},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			if tc.isLive {
				registryGetString = origRegistryGetString
				got, err := HardwareModel()
				if err != nil {
					t.Fatalf("HardwareModel() error = %v, wantErr %v", err, tc.wantErr)
				}
				want, err := Model()
				if err != nil {
					t.Fatalf("Model() error = %v", err)
				}
				if got != strings.ToLower(want) {
					t.Errorf("HardwareModel() = %q, want %q (strings.ToLower(Model()))", got, strings.ToLower(want))
				}
				t.Logf("HardwareModel() on live system = %q", got)
				return
			}

			registryGetString = func(path, name string) (string, error) {
				if path != `HARDWARE\DESCRIPTION\System\BIOS` {
					return "", fmt.Errorf("unexpected registry path: %s", path)
				}
				switch name {
				case "SystemProductName":
					return tc.mockModel, tc.mockModelErr
				case "SystemManufacturer":
					return tc.mockManufacturer, tc.mockMfgErr
				default:
					return "", fmt.Errorf("unexpected value name: %s", name)
				}
			}

			got, err := HardwareModel()
			if (err != nil) != tc.wantErr {
				t.Fatalf("HardwareModel() error = %v, wantErr %v", err, tc.wantErr)
			}
			if got != tc.wantModel {
				t.Errorf("HardwareModel() = %q, want %q", got, tc.wantModel)
			}
		})
	}
}

func TestSite(t *testing.T) {
	origWmiQuery := wmiQuery
	defer func() { wmiQuery = origWmiQuery }()

	tests := []struct {
		name       string
		domain     string
		mockResult []Win32_NTDomain
		queryErr   error
		want       string
		wantErr    bool
	}{
		{
			name:   "Success",
			domain: "some.place.com",
			mockResult: []Win32_NTDomain{
				{
					ClientSiteName:       "NYC",
					DomainControllerName: `\\dc1.some.place.com`,
				},
			},
			want: "NYC",
		},
		{
			name:       "EmptyResult",
			domain:     "some.place.com",
			mockResult: []Win32_NTDomain{},
			want:       "",
		},
		{
			name:     "WMIError",
			domain:   "some.place.com",
			queryErr: errors.New("WMI connection failed"),
			want:     "",
			wantErr:  true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			var queryRan string
			wmiQuery = func(query string, dst any, connectServerArgs ...any) error {
				queryRan = query
				if tt.queryErr != nil {
					return tt.queryErr
				}
				res, ok := dst.(*[]Win32_NTDomain)
				if !ok {
					return fmt.Errorf("unexpected destination type: %T", dst)
				}
				*res = tt.mockResult
				return nil
			}

			got, err := Site(tt.domain)
			if (err != nil) != tt.wantErr {
				t.Fatalf("Site(%q) error = %v, wantErr = %v", tt.domain, err, tt.wantErr)
			}
			if got != tt.want {
				t.Errorf("Site(%q) = %q, want %q", tt.domain, got, tt.want)
			}
			if !strings.Contains(queryRan, fmt.Sprintf("WHERE DomainName='%s'", tt.domain)) {
				t.Errorf("Site(%q) query = %q, did not contain expected WHERE clause", tt.domain, queryRan)
			}
		})
	}
}

func TestTPMVersion(t *testing.T) {
	origGetTPMSpecVersion := getTPMSpecVersion
	defer func() { getTPMSpecVersion = origGetTPMSpecVersion }()

	tests := []struct {
		name    string
		mockVer string
		mockErr error
		want    string
		wantErr bool
	}{
		{
			name:    "Success",
			mockVer: "2.0, 0, 1.38",
			want:    "2.0, 0, 1.38",
		},
		{
			name:    "Error",
			mockErr: errors.New("TBS unavailable"),
			want:    "",
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			getTPMSpecVersion = func() (string, error) {
				return tt.mockVer, tt.mockErr
			}

			got, err := TPMVersion()
			if (err != nil) != tt.wantErr {
				t.Fatalf("TPMVersion() error = %v, wantErr = %v", err, tt.wantErr)
			}
			if got != tt.want {
				t.Errorf("TPMVersion() = %q, want %q", got, tt.want)
			}
		})
	}
}

func TestUserProfiles(t *testing.T) {
	root, err := ioutil.TempDir(os.TempDir(), "")
	if err != nil {
		t.Fatalf("ioutil.TempDir: %v", err)
	}
	defer os.RemoveAll(root)

	users := []string{"Administrator", "George", "Public"}
	for _, u := range users {
		if err := os.MkdirAll(filepath.Join(root, "/Users/", u), 0755); err != nil {
			t.Fatalf("os.MkdirAll: %v", err)
		}
	}
	if err := os.Setenv("SystemDrive", root); err != nil {
		t.Fatalf("os.Setenv: %v", err)
	}
	out, err := UserProfiles()
	if err != nil {
		t.Errorf("UserProfiles() returned unexpected error %v", err)
	}
	if diff := cmp.Diff(out, users); diff != "" {
		t.Errorf("UserProfiles() returned unexpected diff (-want +got):\n%s", diff)
	}
}

func TestUserProfiles_Error(t *testing.T) {
	if err := os.Setenv("SystemDrive", `Z:\NonExistentDirectory_12345`); err != nil {
		t.Fatalf("os.Setenv: %v", err)
	}
	_, err := UserProfiles()
	if err == nil {
		t.Errorf("UserProfiles() returned nil error on non-existent directory, want error")
	}
}
