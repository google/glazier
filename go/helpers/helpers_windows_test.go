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

	"golang.org/x/sys/windows/svc/mgr"
	"golang.org/x/sys/windows/svc"
	so "github.com/iamacarpet/go-win64api/shared"
)

type serviceState int

const (
	stateStopped serviceState = iota
	stateStartPending
	stateRunning
	stateStopPending
)

type fakeService struct {
	state []svc.State
	t     *testing.T
	i     int
}

func (s *fakeService) next() svc.State {
	if s.i >= len(s.state) {
		s.t.Fatalf("ran out of service states...")
	}
	st := s.state[s.i]
	s.i++
	return st
}

func TestRestartServiceWithVerify(t *testing.T) {
	tests := []struct {
		name       string
		states     []svc.State // sequence of states returned by Query
		startState svc.State   // state returned by Control(Stop)
		wantErr    bool
	}{
		{
			"GoodService",
			[]svc.State{svc.Running, svc.Stopped, svc.Running},
			svc.StopPending,
			false,
		},
		{
			"PendingService",
			[]svc.State{svc.Running, svc.Stopped, svc.StartPending, svc.StartPending, svc.Running},
			svc.StopPending,
			false,
		},
		{
			"TimeoutService",
			[]svc.State{svc.Running, svc.Stopped, svc.StartPending, svc.StartPending, svc.StartPending, svc.StartPending, svc.StartPending, svc.StartPending, svc.StartPending, svc.StartPending, svc.StartPending, svc.StartPending, svc.StartPending, svc.StartPending, svc.StartPending},
			svc.StopPending,
			true,
		},
		{
			"AlreadyStoppedService",
			[]svc.State{svc.Stopped, svc.Running},
			svc.Stopped,
			false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			fs := &fakeService{state: tt.states, t: t}
			oldMgrConnect := mgrConnect
			oldMgrDisconnect := mgrDisconnect
			oldMgrOpenService := mgrOpenService
			oldSvcClose := svcClose
			oldSvcConfig := svcConfig
			oldSvcQuery := svcQuery
			oldSvcUpdateConfig := svcUpdateConfig
			oldSvcStart := svcStart
			oldSvcControl := svcControl
			oldTimeSleep := timeSleep
			defer func() {
				mgrConnect = oldMgrConnect
				mgrDisconnect = oldMgrDisconnect
				mgrOpenService = oldMgrOpenService
				svcClose = oldSvcClose
				svcConfig = oldSvcConfig
				svcQuery = oldSvcQuery
				svcUpdateConfig = oldSvcUpdateConfig
				svcStart = oldSvcStart
				svcControl = oldSvcControl
				timeSleep = oldTimeSleep
			}()
			mgrConnect = func() (*mgr.Mgr, error) { return nil, nil }
			mgrDisconnect = func(*mgr.Mgr) error { return nil }
			mgrOpenService = func(*mgr.Mgr, string) (*mgr.Service, error) { return nil, nil }
			svcClose = func(*mgr.Service) error { return nil }
			svcConfig = func(*mgr.Service) (mgr.Config, error) { return mgr.Config{}, nil }
			svcQuery = func(*mgr.Service) (svc.Status, error) {
				return svc.Status{State: fs.next()}, nil
			}
			svcStart = func(*mgr.Service) error { return nil }
			svcControl = func(s *mgr.Service, c svc.Cmd) (svc.Status, error) {
				if c == svc.Stop {
					return svc.Status{State: tt.startState}, nil
				}
				return svc.Status{}, fmt.Errorf("unexpected control code: %v", c)
			}
			timeSleep = func(time.Duration) {}

			err := RestartServiceWithVerify(tt.name, 12)
			if err != nil && !tt.wantErr {
				t.Errorf("RestartServiceWithVerify(%q) returned error: %v, want nil", tt.name, err)
			}
			if err == nil && tt.wantErr {
				t.Errorf("RestartServiceWithVerify(%q) returned nil, want error", tt.name)
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

func TestHasAdmin(t *testing.T) {
	admin, err := HasAdmin()
	if err != nil {
		t.Fatalf("HasAdmin() returned error: %v", err)
	}
	if admin {
		t.Skip("Test running with elevated privileges, skipping check for non-elevated context.")
	}
}
