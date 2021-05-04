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
	"regexp"
	"syscall"
	"testing"
	"time"

	"github.com/google/go-cmp/cmp"
)

func TestExecWithVerify(t *testing.T) {
	err1 := errors.New("direct error")
	tests := []struct {
		ver    *ExecVerifier
		res    ExecResult
		resErr error
		want   error
	}{
		{nil, ExecResult{}, err1, err1},
		{nil, ExecResult{ExitErr: err1}, nil, err1},
		{nil, ExecResult{ExitCode: 1}, nil, ErrExitCode},
		{&ExecVerifier{SuccessCodes: []int{2, 3, 4}}, ExecResult{ExitCode: 3}, nil, nil},
		{&ExecVerifier{SuccessCodes: []int{2, 3, 4}}, ExecResult{ExitCode: 5}, nil, ErrExitCode},
		{nil, ExecResult{
			Stdout: []byte("This is harmless output."),
			Stderr: []byte("This too."),
		}, nil, nil},
		{&ExecVerifier{
			SuccessCodes: []int{0},
			StdOutMatch:  regexp.MustCompile(".*harmful.*"),
			StdErrMatch:  regexp.MustCompile(".*harmful.*"),
		}, ExecResult{
			Stdout: []byte("This is harmless output."),
			Stderr: []byte("This too."),
		}, nil, nil},
		{&ExecVerifier{
			SuccessCodes: []int{0},
			StdOutMatch:  regexp.MustCompile(".*harmful.*"),
			StdErrMatch:  regexp.MustCompile(".*harmful.*"),
		}, ExecResult{
			Stdout: []byte("This is harmful output."),
			Stderr: []byte("This isn't."),
		}, nil, ErrStdOut},
		{&ExecVerifier{
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
		t.Run(fmt.Sprintf(testID, i), func(t *testing.T) {
			execFn = func(p string, a []string, t *time.Duration, s *syscall.SysProcAttr) (ExecResult, error) {
				return tt.res, tt.resErr
			}
			_, got := ExecWithVerify(testID, nil, nil, tt.ver)
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
