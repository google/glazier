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

// Package timers stores points in time to be used for metrics.
package timers

import (
	"fmt"
	"time"

	"golang.org/x/sys/windows/registry"
)

const (
	timerFmt = "2006-01-02 15:04:05.000000+00:00"
)

var (
	// TimersRoot indicates the root Timers registry key.
	TimersRoot = `SOFTWARE\Glazier\Timers`
)

// A Timer stores named time elements.
type Timer struct {
	Name string
	Time time.Time
}

// NewTimer creates a new Timer.
func NewTimer(name string, at *time.Time) *Timer {
	if at == nil {
		t := time.Now().UTC()
		at = &t
	}
	return &Timer{Name: name, Time: *at}
}

// Load loads a timer object into the registry.
func (t *Timer) Load() error {
	k, err := registry.OpenKey(registry.LOCAL_MACHINE, TimersRoot, registry.QUERY_VALUE)
	if err != nil {
		return fmt.Errorf("reg.OpenKey: %w", err)
	}
	defer k.Close()
	v, _, err := k.GetStringValue("TIMER_" + t.Name)
	if err != nil {
		return fmt.Errorf("GetStringValue: %w", err)
	}
	p, err := time.Parse(timerFmt, v)
	if err != nil {
		return fmt.Errorf("time.Parse: %w", err)
	}
	t.Time = p
	return nil
}

// Record records a timer object into the registry.
func (t *Timer) Record() error {
	k, _, err := registry.CreateKey(registry.LOCAL_MACHINE, TimersRoot, registry.WRITE)
	if err != nil {
		return err
	}
	defer k.Close()
	return k.SetStringValue("TIMER_"+t.Name, t.TimeString())
}

// TimeString renders a timer's time value with the default formatting.
func (t *Timer) TimeString() string {
	return t.Time.Format(timerFmt)
}
