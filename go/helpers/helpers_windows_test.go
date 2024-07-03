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

package helpers

import (
	"errors"
	"fmt"
	"regexp"
	"testing"
	"time"

	so "github.com/iamacarpet/go-win64api/shared"
)

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
