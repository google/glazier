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

package join

import (
	"errors"
	"runtime"
	"syscall"
	"testing"

	"golang.org/x/sys/windows"
)

type joinMock struct {
	retCode uintptr
	err     error
}

func (m *joinMock) mockNetJoinDomain(a ...uintptr) (uintptr, uintptr, error) {
	return m.retCode, 0, m.err
}

func TestDomain(t *testing.T) {
	defer func() { netJoinDomain = prodNetJoinDomain.Call }()
	tests := []struct {
		name    string
		retCode uintptr
		err     error
		wantErr bool
	}{
		{
			name:    "success",
			retCode: 0,
		},
		{
			name:    "failure",
			retCode: 1355, // ERROR_NO_SUCH_DOMAIN
			err:     syscall.Errno(1355),
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			m := joinMock{retCode: tt.retCode, err: tt.err}
			netJoinDomain = m.mockNetJoinDomain
			err := Domain("domain", "ou", "account", "password", DomainJoinOptions(JoinDomainFlag))
			if !tt.wantErr && err != nil {
				t.Errorf("Domain() returned unexpected error: %v", err)
			}
			if tt.wantErr && err == nil {
				t.Errorf("Domain() returned success, want error")
			}
		})
	}
}

func TestDomainLive(t *testing.T) {
	if runtime.GOOS != "windows" {
		t.Skip("Skipping live domain join test on non-Windows OS")
	}
	// Ensure we are using the real Windows API for this test.
	netJoinDomain = prodNetJoinDomain.Call
	t.Log("Attempting live domain join against Windows API; this requires elevation and will fail with dummy data.")

	tests := []struct {
		name        string
		domain      string
		ou          string
		account     string
		pass        string
		wantErr     bool
		wantErrCode windows.Errno
	}{
		{
			name:        "Live API call with dummy data",
			domain:      "non-existent-domain-12345",
			ou:          "OU=Computers",
			account:     "noaccount",
			pass:        "nopass",
			wantErr:     true, // Expect failure
			wantErrCode: 1355, // ERROR_NO_SUCH_DOMAIN
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := Domain(tt.domain, tt.ou, tt.account, tt.pass, DomainJoinOptions(JoinDomainFlag))
			if !tt.wantErr && err != nil {
				t.Errorf("Domain() returned unexpected error: %v", err)
			}
			if tt.wantErr && err == nil {
				t.Errorf("Domain() returned success, want error")
			}
			if tt.wantErr && err != nil && !errors.Is(err, tt.wantErrCode) {
				t.Errorf("Domain() returned error %v, want error code %d", err, tt.wantErrCode)
			}
			t.Logf("Domain(%q, %q, %q, ...) returned: %v", tt.domain, tt.ou, tt.account, err)
		})
	}
}
