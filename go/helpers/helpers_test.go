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
