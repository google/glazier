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

package googet

import (
	"errors"
	"testing"
	"time"

	"github.com/google/go-cmp/cmp"
	"github.com/google/glazier/go/helpers"
)

func TestInstall(t *testing.T) {
	tests := []struct {
		pkg       string
		sources   string
		reinstall bool
		wantArg   []string
		wantErr   error
	}{
		{
			pkg:       "pkg-one",
			sources:   "http://repo/manifest/url",
			reinstall: false,
			wantArg:   []string{"-noconfirm", "install", "--sources", "http://repo/manifest/url", "pkg-one"},
			wantErr:   nil,
		},
		{
			pkg:       "pkg-two",
			sources:   "",
			reinstall: true,
			wantArg:   []string{"-noconfirm", "install", "--reinstall", "pkg-two"},
			wantErr:   nil,
		},
	}
	for _, tt := range tests {
		a := []string{}
		funcExec = func(path string, args []string, timeout *time.Duration, v *helpers.ExecVerifier) (helpers.ExecResult, error) {
			a = args
			return helpers.ExecResult{}, nil
		}
		err := Install(tt.pkg, tt.sources, tt.reinstall, nil)
		if !cmp.Equal(a, tt.wantArg) {
			t.Errorf("Install(%s) produced unexpected differences (-want +got): %s", tt.pkg, cmp.Diff(tt.wantArg, a))
		}
		if !errors.Is(err, tt.wantErr) {
			t.Errorf("Install(%s) returned unexpected error %v", tt.pkg, err)
		}
	}
}

func TestPackageVersion(t *testing.T) {
	fail := errors.New("test failure")
	tests := []struct {
		in      helpers.ExecResult
		inErr   error
		want    string
		wantErr error
	}{
		{
			in: helpers.ExecResult{
				ExitErr: nil,
				Stdout: []byte(`
Installed packages matching "foo":
  foo.x86_64 2.6.0-20191015@281551337
	`),
				Stderr: []byte(""),
			},
			want:    "2.6.0-20191015@281551337",
			wantErr: nil,
		},
		{
			in: helpers.ExecResult{
				ExitErr: nil,
				Stdout: []byte(`
Installed packages matching "foo":
  foo.x86_64 2021.03.01@360244395
`),
				Stderr: []byte(""),
			},
			want:    "2021.03.01@360244395",
			wantErr: nil,
		},
		{
			in: helpers.ExecResult{
				ExitErr: nil,
				Stdout: []byte(`
Installed packages matching "foo-tools":
  foo-tools.x86_64 20210203@355474486
`),
				Stderr: []byte(""),
			},
			want:    "20210203@355474486",
			wantErr: nil,
		},
		{
			in: helpers.ExecResult{
				ExitErr: nil,
				Stdout: []byte(`
Installed packages matching "missing":
No package matching filter "missing" installed.
`),
				Stderr: []byte(""),
			},
			want:    "",
			wantErr: nil,
		},
		{
			in: helpers.ExecResult{
				ExitErr: fail,
				Stdout:  []byte(""),
				Stderr:  []byte(""),
			},
			inErr:   fail,
			want:    "unknown",
			wantErr: fail,
		},
	}
	for _, tt := range tests {
		funcExec = func(path string, args []string, timeout *time.Duration, v *helpers.ExecVerifier) (helpers.ExecResult, error) {
			return tt.in, tt.inErr
		}
		o, err := PackageVersion("")
		if o != tt.want {
			t.Errorf("PackageVersion() = %q, want %q", o, tt.want)
		}
		if !errors.Is(err, tt.wantErr) {
			t.Errorf("PackageVersion() returned unexpected error %v", err)
		}
	}
}
