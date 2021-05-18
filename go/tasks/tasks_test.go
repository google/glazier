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
	"testing"

	"github.com/capnspacehook/taskmaster"
)

func TestTaskExists(t *testing.T) {
	tests := []struct {
		desc string
		in   string
		coll taskmaster.RegisteredTaskCollection
		want bool
	}{
		{
			desc: "task error",
			in:   "task1",
			coll: taskmaster.RegisteredTaskCollection{
				taskmaster.RegisteredTask{Name: "Task1"},
				taskmaster.RegisteredTask{Name: "task2"},
			},
			want: true,
		},
		{
			desc: "task does not exist",
			in:   "task2",
			coll: taskmaster.RegisteredTaskCollection{
				taskmaster.RegisteredTask{Name: "Task1"},
				taskmaster.RegisteredTask{Name: "task3"},
			},
			want: false,
		},
	}
	for _, tt := range tests {
		tt := tt
		t.Run(tt.desc, func(t *testing.T) {
			t.Parallel()
			got := taskMatcher(tt.in, tt.coll)
			if got != tt.want {
				t.Errorf("taskMatcher(%v) = %v, want %v", tt.in, got, tt.want)
			}
		})
	}
}
