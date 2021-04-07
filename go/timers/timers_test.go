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
package timers

import (
	"fmt"
	"testing"
	"time"

	"github.com/google/go-cmp/cmp"
	"golang.org/x/sys/windows/registry"
)

func TestTimeString(t *testing.T) {
	tests := []struct {
		name string
		tm   time.Time
		want string
	}{
		{"Test1", time.Date(2020, 06, 14, 22, 33, 52, 519578000, time.UTC), "2020-06-14 22:33:52.519578+00:00"},
		{"Test2", time.Date(2021, 01, 14, 23, 33, 52, 466850000, time.UTC), "2021-01-14 23:33:52.466850+00:00"},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			timer := Timer{Name: tt.name, Time: tt.tm}
			out := timer.TimeString()
			if !cmp.Equal(tt.want, out) {
				t.Errorf("TimeString(%s) produced unexpected diff %v", tt.name, cmp.Diff(tt.want, out))
			}
		})
	}
}

func getTimer(key string) (string, error) {
	k, _, err := registry.CreateKey(registry.LOCAL_MACHINE, TimersRoot, registry.QUERY_VALUE)
	if err != nil {
		return "", err
	}
	defer k.Close()
	v, _, err := k.GetStringValue("TIMER_" + key)
	return v, err
}

func setTimer(key, value string) error {
	k, _, err := registry.CreateKey(registry.LOCAL_MACHINE, TimersRoot, registry.ALL_ACCESS)
	if err != nil {
		return err
	}
	defer k.Close()
	k.SetStringValue("TIMER_"+key, value)
	return nil
}

func delTimer(key string) {
	registry.DeleteKey(registry.LOCAL_MACHINE, fmt.Sprintf(`%s\TIMER_%s`, TimersRoot, key))
}

func TestLoad(t *testing.T) {
	tests := []struct {
		name string
		in   string
		want time.Time
	}{
		{"Test1", "2020-06-14 22:33:52.519578+00:00", time.Date(2020, 06, 14, 22, 33, 52, 519578000, time.UTC)},
		{"Test2", "2021-01-14 23:33:52.466850+00:00", time.Date(2021, 01, 14, 23, 33, 52, 466850000, time.UTC)},
	}
	TimersRoot = `SOFTWARE\TEST\Glazier\Timers`
	for _, tt := range tests {

		if err := setTimer(tt.name, tt.in); err != nil {
			t.Errorf("setTimer(%s) produced unexpected error %v", tt.name, err)

		}
		defer delTimer(tt.name)
		timer := Timer{Name: tt.name}
		err := timer.Load()
		if err != nil {
			t.Errorf("Verifying timer.Load(%s) returned unexpected error %v", tt.name, err)
		}
		if cmp.Diff(tt.want, timer.Time) != "" {
			t.Errorf("timer.Load(%s) produced unexpected diff %v", tt.name, cmp.Diff(tt.want, timer.Time))
		}
	}
}

func TestRecord(t *testing.T) {
	tests := []struct {
		name string
		in   time.Time
		want string
	}{
		{"Test3", time.Date(2020, 06, 14, 22, 33, 52, 519578000, time.UTC), "2020-06-14 22:33:52.519578+00:00"},
		{"Test4", time.Date(2021, 02, 19, 23, 33, 52, 466850000, time.UTC), "2021-02-19 23:33:52.466850+00:00"},
	}
	TimersRoot = `SOFTWARE\TEST\Glazier\Timers`
	for _, tt := range tests {
		defer delTimer(tt.name)
		timer := Timer{Name: tt.name, Time: tt.in}
		err := timer.Record()
		if err != nil {
			t.Errorf("timer.Record(%s) returned unexpected error %v", tt.name, err)
		}
		out, err := getTimer(tt.name)
		if err != nil {
			t.Errorf("getTimer(%s) produced unexpected error %v", tt.name, err)
		}
		if cmp.Diff(tt.want, out) != "" {
			t.Errorf("timer.Record(%s) produced unexpected diff %v", tt.name, cmp.Diff(tt.want, out))
		}
	}
}
