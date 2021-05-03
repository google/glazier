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

package tasks

import (
	"errors"
	"testing"

	"github.com/capnspacehook/taskmaster"
)

func TestTaskExists(t *testing.T) {
	lookupErr := errors.New("scheduled task lookup failed")
	tests := []struct {
		desc     string
		in       string
		fakeTask func(name string) (taskmaster.RegisteredTask, error)
		want     bool
		wantErr  error
	}{
		{
			desc: "task error",
			in:   "task1",
			fakeTask: func(name string) (taskmaster.RegisteredTask, error) {
				return taskmaster.RegisteredTask{}, lookupErr
			},
			want:    false,
			wantErr: lookupErr,
		},
		{
			desc: "task does not exist",
			in:   "task2",
			fakeTask: func(name string) (taskmaster.RegisteredTask, error) {
				return taskmaster.RegisteredTask{}, nil
			},
			want:    false,
			wantErr: nil,
		},
		{
			desc: "task is not registered",
			in:   "task3",
			fakeTask: func(name string) (taskmaster.RegisteredTask, error) {
				return taskmaster.RegisteredTask{}, ErrNotRegistered
			},
			want:    false,
			wantErr: nil,
		},
		{
			desc: "task does exist",
			in:   "task4",
			fakeTask: func(name string) (taskmaster.RegisteredTask, error) {
				return taskmaster.RegisteredTask{
					Name: "task4",
				}, nil
			},
			want:    true,
			wantErr: nil,
		},
	}

	for _, tt := range tests {
		t.Run(tt.desc, func(t *testing.T) {
			fnGetTask = tt.fakeTask
			got, err := TaskExists(tt.in)

			if !errors.Is(err, tt.wantErr) {
				t.Errorf("TaskExists(%v) returned unexpected error %v", tt.in, err)
			}
			if got != tt.want {
				t.Errorf("TaskExists(%v) = %v, want %v", tt.in, got, tt.want)
			}
		})
	}
}
