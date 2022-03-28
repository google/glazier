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
		funcExec = func(path string, args []string, v *helpers.ExecConfig) (helpers.ExecResult, error) {
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

func TestInstalled(t *testing.T) {
	fail := errors.New("test failure")
	tests := []struct {
		desc    string
		in      helpers.ExecResult
		inErr   error
		want    []Package
		wantErr error
	}{
		{
			desc: "normal output with matches",
			in: helpers.ExecResult{
				ExitErr: nil,
				Stdout: []byte(`Installed packages:
  aukera.x86_64 2021.06.08@12345
  cabbie.x86_64 2021.05.26@67890
  glazier.noarch 1.5.3@9872313

	`),
			},
			want: []Package{
				Package{"aukera.x86_64", "2021.06.08@12345"},
				Package{"cabbie.x86_64", "2021.05.26@67890"},
				Package{"glazier.noarch", "1.5.3@9872313"},
			},
			wantErr: nil,
		},
		{
			desc: "no matching packages",
			in: helpers.ExecResult{
				ExitErr: fail,
				Stdout: []byte(`Installed packages matching "foo":
No package matching filter "foo" installed.
`),
			},
			inErr:   fail,
			want:    []Package{},
			wantErr: fail,
		},
	}
	for _, tt := range tests {
		funcExec = func(path string, args []string, v *helpers.ExecConfig) (helpers.ExecResult, error) {
			return tt.in, tt.inErr
		}
		o, err := Installed("", nil)
		diff := cmp.Diff(tt.want, o)
		if diff != "" {
			t.Errorf("Installed(%s) diff = %v", tt.desc, diff)
		}
		if !errors.Is(err, tt.wantErr) {
			t.Errorf("Installed(%s) returned unexpected error %v", tt.desc, err)
		}
	}
}

func TestListRepos(t *testing.T) {
	fail := errors.New("test failure")
	tests := []struct {
		desc    string
		in      helpers.ExecResult
		inErr   error
		want    []Repo
		wantErr error
	}{
		{
			desc: "normal output with matches",
			in: helpers.ExecResult{
				ExitErr: nil,
				Stdout: []byte(`C:\ProgramData\GooGet\repos\first_set.repo:
  repo-one:  https://googet-server.example.com/univ/repos/first
  repo-two: https://googet-server.example.com/univ/repos/second
C:\ProgramData\GooGet\repos\second_set.repo:
  repo-three:  https://googet-server.example.com/univ/repos/third
	`),
			},
			want: []Repo{
				Repo{"repo-one", "https://googet-server.example.com/univ/repos/first"},
				Repo{"repo-two", "https://googet-server.example.com/univ/repos/second"},
				Repo{"repo-three", "https://googet-server.example.com/univ/repos/third"},
			},
			wantErr: nil,
		},
		{
			desc: "zero repos",
			in: helpers.ExecResult{
				ExitErr: nil,
				Stdout:  []byte(``),
			},
			want:    []Repo{},
			wantErr: nil,
		},
		{
			desc: "execution error",
			in: helpers.ExecResult{
				ExitErr: fail,
				Stdout:  []byte(``),
			},
			inErr:   fail,
			want:    []Repo{},
			wantErr: fail,
		},
	}
	for _, tt := range tests {
		funcExec = func(path string, args []string, v *helpers.ExecConfig) (helpers.ExecResult, error) {
			return tt.in, tt.inErr
		}
		o, err := ListRepos(nil)
		diff := cmp.Diff(tt.want, o)
		if diff != "" {
			t.Errorf("ListRepos(%s) diff = %v", tt.desc, diff)
		}
		if !errors.Is(err, tt.wantErr) {
			t.Errorf("ListRepos(%s) returned unexpected error %v", tt.desc, err)
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
		funcExec = func(path string, args []string, v *helpers.ExecConfig) (helpers.ExecResult, error) {
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
