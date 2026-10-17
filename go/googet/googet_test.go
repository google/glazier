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
	"runtime"
	"strings"
	"testing"

	"github.com/google/go-cmp/cmp"
	"github.com/google/glazier/go/helpers"
)

func TestNewConfigGooGetExe(t *testing.T) {
	tests := []struct {
		desc       string
		machine    string
		machineErr error
		env        string
		want       string
		// windowsOnly skips the case on other platforms.
		windowsOnly bool
	}{
		{desc: "machine value wins", machine: `C:\ProgramData\GooGet`, env: `C:\Users\Public\GooGet`, want: `C:\ProgramData\GooGet\googet.exe`},
		{desc: "environment fallback", machineErr: errors.New("not found"), env: `C:\GooGet`, want: `C:\GooGet\googet.exe`},
		{desc: "empty machine value", env: `C:\GooGet`, want: `C:\GooGet\googet.exe`},
		{desc: "no root", machineErr: errors.New("not found"), want: ""},
		{desc: "relative root", machineErr: errors.New("not found"), env: "GooGet", want: "", windowsOnly: true},
		{desc: "relative machine value", machine: "GooGet", env: `C:\GooGet`, want: `C:\GooGet\googet.exe`, windowsOnly: true},
	}
	orig := funcMachineGooGetRoot
	t.Cleanup(func() { funcMachineGooGetRoot = orig })
	for _, tt := range tests {
		t.Run(tt.desc, func(t *testing.T) {
			if tt.windowsOnly && runtime.GOOS != "windows" {
				t.Skip("filepath.IsAbs knows drive letters only on Windows")
			}
			funcMachineGooGetRoot = func() (string, error) { return tt.machine, tt.machineErr }
			t.Setenv("GooGetRoot", tt.env)
			conf := NewConfig()
			if got := conf.GooGetExe; got != tt.want {
				t.Errorf("NewConfig().GooGetExe = %q, want %q", got, tt.want)
			}
			if got, want := conf.Root, strings.TrimSuffix(tt.want, `\googet.exe`); got != want {
				t.Errorf("NewConfig().Root = %q, want %q", got, want)
			}
		})
	}
}

func TestCommandsPassRoot(t *testing.T) {
	origExec := funcExec
	origRoot := funcMachineGooGetRoot
	t.Cleanup(func() {
		funcExec = origExec
		funcMachineGooGetRoot = origRoot
	})
	var gotPath string
	var gotArgs []string
	funcExec = func(path string, args []string, v *helpers.ExecConfig) (helpers.ExecResult, error) {
		gotPath = path
		gotArgs = args
		return helpers.ExecResult{}, nil
	}
	funcMachineGooGetRoot = func() (string, error) { return `X:\machine`, nil }
	t.Setenv("GooGetRoot", `X:\env`)

	conf := &Config{GooGetExe: `X:\conf\googet.exe`, Root: `X:\conf`}
	tests := []struct {
		desc     string
		run      func() error
		wantPath string
		wantArgs []string
	}{
		{
			desc:     "call",
			run:      func() error { return Update(conf) },
			wantPath: `X:\conf\googet.exe`,
			wantArgs: []string{"-root", `X:\conf`, "-noconfirm", "update"},
		},
		{
			desc:     "Installed",
			run:      func() error { _, err := Installed("pkg", conf); return err },
			wantPath: `X:\conf\googet.exe`,
			wantArgs: []string{"-root", `X:\conf`, "installed", "pkg"},
		},
		{
			desc:     "ListRepos",
			run:      func() error { _, err := ListRepos(conf); return err },
			wantPath: `X:\conf\googet.exe`,
			wantArgs: []string{"-root", `X:\conf`, "listrepos"},
		},
		{
			desc:     "PackageVersion uses the machine root",
			run:      func() error { _, err := PackageVersion("pkg"); return err },
			wantPath: `X:\machine\googet.exe`,
			wantArgs: []string{"-root", `X:\machine`, "installed", "pkg"},
		},
		{
			desc:     "nil config uses the machine root",
			run:      func() error { return Update(nil) },
			wantPath: `X:\machine\googet.exe`,
			wantArgs: []string{"-root", `X:\machine`, "-noconfirm", "update"},
		},
		{
			desc:     "no root",
			run:      func() error { return Update(&Config{GooGetExe: `X:\conf\googet.exe`}) },
			wantPath: `X:\conf\googet.exe`,
			wantArgs: []string{"-noconfirm", "update"},
		},
	}
	for _, tt := range tests {
		t.Run(tt.desc, func(t *testing.T) {
			if err := tt.run(); err != nil {
				t.Fatalf("%s returned error: %v", tt.desc, err)
			}
			if gotPath != tt.wantPath {
				t.Errorf("%s ran %q, want %q", tt.desc, gotPath, tt.wantPath)
			}
			if diff := cmp.Diff(tt.wantArgs, gotArgs); diff != "" {
				t.Errorf("%s args mismatch (-want +got):\n%s", tt.desc, diff)
			}
		})
	}
}

func TestInstall(t *testing.T) {
	tests := []struct {
		pkg       string
		sources   string
		reinstall bool
		dbOnly    bool
		wantArg   []string
		wantErr   error
	}{
		{
			pkg:       "pkg-one",
			sources:   "http://repo/manifest/url",
			reinstall: false,
			dbOnly:    false,
			wantArg:   []string{"-noconfirm", "install", "-sources", "http://repo/manifest/url", "pkg-one"},
			wantErr:   nil,
		},
		{
			pkg:       "pkg-two",
			sources:   "",
			reinstall: true,
			dbOnly:    false,
			wantArg:   []string{"-noconfirm", "install", "-reinstall", "pkg-two"},
			wantErr:   nil,
		},
		{
			pkg:       "pkg-three",
			sources:   "",
			reinstall: false,
			dbOnly:    true,
			wantArg:   []string{"-noconfirm", "install", "-db_only", "pkg-three"},
			wantErr:   nil,
		},
	}
	// Without a GooGet root, the commands pass no -root flag.
	origRoot := funcMachineGooGetRoot
	t.Cleanup(func() { funcMachineGooGetRoot = origRoot })
	funcMachineGooGetRoot = func() (string, error) { return "", errors.New("not found") }
	t.Setenv("GooGetRoot", "")
	for _, tt := range tests {
		a := []string{}
		funcExec = func(path string, args []string, v *helpers.ExecConfig) (helpers.ExecResult, error) {
			a = args
			return helpers.ExecResult{}, nil
		}
		err := Install(tt.pkg, tt.sources, tt.reinstall, tt.dbOnly, nil)
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
