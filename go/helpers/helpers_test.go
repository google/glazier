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

package helpers

import (
	"errors"
	"fmt"
	"io/ioutil"
	"os"
	"path/filepath"
	"regexp"
	"testing"
	"time"

	"github.com/google/go-cmp/cmp"
	so "github.com/iamacarpet/go-win64api/shared"
)

func TestVerify(t *testing.T) {
	err1 := errors.New("direct error")
	def := NewExecVerifier()
	tests := []struct {
		ver    ExecVerifier
		res    ExecResult
		resErr error
		want   error
	}{
		{*def, ExecResult{}, err1, err1},
		{*def, ExecResult{ExitErr: err1}, nil, err1},
		{*def, ExecResult{ExitCode: 1}, nil, ErrExitCode},
		{ExecVerifier{SuccessCodes: []int{2, 3, 4}}, ExecResult{ExitCode: 3}, nil, nil},
		{ExecVerifier{SuccessCodes: []int{2, 3, 4}}, ExecResult{ExitCode: 5}, nil, ErrExitCode},
		{*def, ExecResult{
			Stdout: []byte("This is harmless output."),
			Stderr: []byte("This too."),
		}, nil, nil},
		{ExecVerifier{
			SuccessCodes: []int{0},
			StdOutMatch:  regexp.MustCompile(".*harmful.*"),
			StdErrMatch:  regexp.MustCompile(".*harmful.*"),
		}, ExecResult{
			Stdout: []byte("This is harmless output."),
			Stderr: []byte("This too."),
		}, nil, nil},
		{ExecVerifier{
			SuccessCodes: []int{0},
			StdOutMatch:  regexp.MustCompile(".*harmful.*"),
			StdErrMatch:  regexp.MustCompile(".*harmful.*"),
		}, ExecResult{
			Stdout: []byte("This is harmful output."),
			Stderr: []byte("This isn't."),
		}, nil, ErrStdOut},
		{ExecVerifier{
			SuccessCodes: []int{0},
			StdOutMatch:  regexp.MustCompile(".*harmful.*"),
			StdErrMatch:  regexp.MustCompile(".*harmful.*"),
		}, ExecResult{
			Stderr: []byte("This is harmful output."),
			Stdout: []byte("This isn't."),
		}, nil, ErrStdErr},
	}
	for i, tt := range tests {
		testID := fmt.Sprintf("Test%d", i)
		t.Run(testID, func(t *testing.T) {
			_, got := verify(testID, tt.res, tt.resErr, tt.ver)
			if !errors.Is(got, tt.want) {
				t.Errorf("got %v; want %v", got, tt.want)
			}
		})
	}
}

func TestExecWithRetry(t *testing.T) {
	tests := []struct {
		desc    string
		inConf  *ExecConfig
		inErr   []error
		inRes   []ExecResult
		wantErr error
		wantRes ExecResult
	}{
		{"defaults used; success on first try", nil, []error{nil},
			[]ExecResult{
				ExecResult{Stdout: []byte("Result 1")},
			}, nil,
			ExecResult{Stdout: []byte("Result 1")},
		},
		{"defaults used; error on first try", nil, []error{ErrStdErr},
			[]ExecResult{
				ExecResult{Stdout: []byte("Result 1")},
			}, ErrStdErr,
			ExecResult{},
		},
		{"success on third try", &ExecConfig{RetryCount: 3},
			[]error{ErrStdErr, ErrStdErr, nil},
			[]ExecResult{
				ExecResult{Stdout: []byte("Result 1")},
				ExecResult{Stdout: []byte("Result 2")},
				ExecResult{Stdout: []byte("Result 3")},
			}, nil,
			ExecResult{Stdout: []byte("Result 3")},
		},
	}
	fnSleep = func(time.Duration) {}
	for _, tt := range tests {
		t.Run(tt.desc, func(t *testing.T) {
			t.Parallel()
			ci := -1
			fnExec = func(string, []string, *ExecConfig) (ExecResult, error) {
				ci++
				if ci >= len(tt.inErr) {
					t.Fatalf("ran out of return values...")
				}
				return tt.inRes[ci], tt.inErr[ci]
			}
			got, err := Exec("test-process", []string{}, tt.inConf)
			if !errors.Is(err, tt.wantErr) {
				t.Errorf("Exec(%s): got %v; want %v", tt.desc, err, tt.wantErr)
			}
			diff := cmp.Diff(got, tt.wantRes)
			if err == nil && diff != "" {
				t.Errorf("Exec(%s): returned unexpected differences (-want +got):\n%s", tt.desc, diff)
			}
		})
	}
}

func TestWaitForProcessExit(t *testing.T) {
	tests := []struct {
		match   string
		plists  [][]so.Process
		timeout time.Duration
		want    error
	}{
		// not running
		{"proc1", [][]so.Process{
			[]so.Process{
				so.Process{Executable: "proc2"},
				so.Process{Executable: "otherproc"},
			},
			[]so.Process{
				so.Process{Executable: "proc2"},
				so.Process{Executable: "otherproc"},
			},
		}, 20 * time.Second, nil},
		// stops within timeout
		{"proc2", [][]so.Process{
			[]so.Process{
				so.Process{Executable: "otherproc"},
				so.Process{Executable: "proc2"},
			},
			[]so.Process{
				so.Process{Executable: "otherproc"},
				so.Process{Executable: "proc1"},
			},
		}, 20 * time.Second, nil},
		// never stops
		{"proc2", [][]so.Process{
			[]so.Process{
				so.Process{Executable: "proc2"},
				so.Process{Executable: "otherproc"},
			},
			[]so.Process{
				so.Process{Executable: "proc2"},
				so.Process{Executable: "otherproc"},
			},
			[]so.Process{
				so.Process{Executable: "proc2"},
				so.Process{Executable: "otherproc"},
			},
			[]so.Process{
				so.Process{Executable: "proc2"},
				so.Process{Executable: "otherproc"},
			},
		}, 15 * time.Second, ErrTimeout},
	}
	for i, tt := range tests {
		t.Run(fmt.Sprintf("Test%d", i), func(t *testing.T) {
			ci := -1
			fnProcessList = func() ([]so.Process, error) {
				ci++
				if ci >= len(tt.plists) {
					t.Fatalf("ran out of return values...")
				}
				return tt.plists[ci], nil
			}
			re := regexp.MustCompile(tt.match)
			got := WaitForProcessExit(re, tt.timeout)
			if !errors.Is(got, tt.want) {
				t.Errorf("got %v; want %v", got, tt.want)
			}
		})
	}
}

func TestContainsString(t *testing.T) {
	tests := []struct {
		in    []string
		inStr string
		want  bool
	}{
		{
			in:    []string{"abc", "def", "ghi"},
			inStr: "def",
			want:  true,
		},
		{
			in:    []string{"abc", "def", "ghi"},
			inStr: "d",
			want:  false,
		},
		{
			in:    []string{"abc", "def", "ghi"},
			inStr: "",
			want:  false,
		},
	}
	for _, tt := range tests {
		o := ContainsString(tt.inStr, tt.in)
		if o != tt.want {
			t.Errorf("ContainsString(%s, %v) = %t, want %t", tt.inStr, tt.in, o, tt.want)
		}
	}
}

// TestStringToSlice ensures StringToSlice correctly parses passed params
func TestStringToSlice(t *testing.T) {
	tests := []struct {
		desc string
		in   string
		out  []string
	}{
		{
			desc: "comma separated",
			in:   "a,b,c",
			out:  []string{"a", "b", "c"},
		},
		{
			desc: "comma separated with spaces",
			in:   "a, b, c",
			out:  []string{"a", "b", "c"},
		},
		{
			desc: "space separated",
			in:   "a b c",
			out:  []string{"a b c"},
		},
		{
			desc: "trailing whitespace",
			in:   "a b c ",
			out:  []string{"a b c"},
		},
		{
			desc: "semicolon separated",
			in:   "a;b;c",
			out:  []string{"a;b;c"},
		},
	}
	for _, tt := range tests {
		o := StringToSlice(tt.in)
		if diff := cmp.Diff(o, tt.out); diff != "" {
			t.Errorf("TestStringToSlice(): %+v returned unexpected differences (-want +got):\n%s", tt.desc, diff)
		}
	}
}

func TestStringToMap(t *testing.T) {
	tests := []struct {
		desc string
		in   string
		out  map[string]bool
	}{
		{
			desc: "comma separated",
			in:   "a,b,c",
			out:  map[string]bool{"a": true, "b": true, "c": true},
		},
		{
			desc: "comma separated with spaces",
			in:   "a, b, c",
			out:  map[string]bool{"a": true, "b": true, "c": true},
		},
		{
			desc: "space separated",
			in:   "a b c",
			out:  map[string]bool{"a b c": true},
		},
		{
			desc: "trailing whitespace",
			in:   "a b c ",
			out:  map[string]bool{"a b c": true},
		},
		{
			desc: "semicolon separated",
			in:   "a;b;c",
			out:  map[string]bool{"a;b;c": true},
		},
		{
			desc: "empty string",
			in:   "",
			out:  map[string]bool{},
		},
	}
	for _, tt := range tests {
		o := StringToMap(tt.in)
		if diff := cmp.Diff(o, tt.out); diff != "" {
			t.Errorf("TestStringToSlice(): %+v returned unexpected differences (-want +got):\n%s", tt.desc, diff)
		}
	}
}

func TestUnzip(t *testing.T) {
	out := os.TempDir()

	zip := "testdata/test.zip"

	if err := Unzip(zip, out); err != nil {
		t.Fatalf("Unzip: %v", err)
	}
	f, err := ioutil.ReadFile(filepath.Join(out, "google.txt"))
	if err != nil {
		t.Fatalf("failed reading expected output file: %v", err)
	}
	got := string(f)
	want := "i'm feeling lucky"
	if got != want {
		t.Fatalf("unzip output: %s, want %s", got, want)
	}
}
