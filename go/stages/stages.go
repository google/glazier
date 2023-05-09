// Copyright 2020 Google LLC
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

// Package stages allows interacting with Glazier build stages.
package stages

import (
	"fmt"
	"strconv"
	"time"

	"github.com/pkg/errors"
	"github.com/google/glazier/go/registry"
)

const (
	// StartKey references the time that the stage started
	StartKey = "Start"
	// EndKey references the time that the stage ended
	EndKey = "End"
	// TermStage after which to consider the build completed
	TermStage = "100"
	// RegStagesRoot references the root Registry key under which stages exist
	RegStagesRoot = `SOFTWARE\Glazier\Stages`

	defaultTimeout = 60 * 24 * 7 * time.Minute // 7 days
	regActiveKey   = "_Active"
	timeFmt        = "2006-01-02T15:04:05.000000"
)

var (
	// ErrPeriod indicates an unsupported period was passed when checking stage status
	ErrPeriod = errors.New("invalid period")
)

// A Stage stores named stage elements.
type Stage struct {
	ID    string
	Start time.Time
	End   time.Time
	State string
}

// NewStage fills the stage struct with default values.
func NewStage() *Stage {
	return &Stage{
		State: "Unknown",
	}
}

func activeTimeFromReg(root, stageID string, period string) (time.Time, error) {
	switch period {
	case StartKey, EndKey:
		active, err := registry.GetString(fmt.Sprintf(`%s\%s`, root, stageID), period)
		if err != nil && err != registry.ErrNotExist {
			return time.Time{}, err
		}

		var at time.Time
		if active != "" {
			at, err = time.Parse(timeFmt, active)
			if err != nil {
				return time.Time{}, err
			}
		}
		return at, nil
	default:
		return time.Time{}, ErrPeriod
	}
}

// RetreiveTimes populates the Stage struct with the start and end times of the
// passed stage ID.
func (s *Stage) RetreiveTimes(root, stageID string) error { // go/LEGACY_TYPO
	var err error

	if s.Start, err = activeTimeFromReg(root, stageID, StartKey); err != nil {
		return err
	}

	if s.End, err = activeTimeFromReg(root, stageID, EndKey); err != nil {
		return err
	}

	return nil
}

func checkExpiration(stageID string) error {
	// TODO(b/139666887): Implement stage expiration here
	s := NewStage()
	return s.RetreiveTimes(RegStagesRoot, stageID) // go/LEGACY_TYPO
}

func activeStageFromReg(root string) (string, error) {
	active, err := registry.GetString(root, regActiveKey)
	if err != nil {
		if err != registry.ErrNotExist {
			return "", err
		}
		return "0", nil
	}
	return active, nil
}

// ActiveStage returns the active build stage string converted to uint64.
// The returned uint64 can be used for comparison against greater/lesser
// stages to determine the latest stage.
func ActiveStage() (uint64, error) {
	s, err := activeStageFromReg(RegStagesRoot)
	if err != nil {
		return 0, err
	}
	err = checkExpiration(s)
	if err != nil {
		return 0, err
	}

	return strconv.ParseUint(s, 10, 64)
}

// ActiveStatus returns a Stage struct with all known fields.
func ActiveStatus() (*Stage, error) {
	var err error
	s := NewStage()

	s.ID, err = activeStageFromReg(RegStagesRoot)
	if err != nil {
		return s, err
	}

	// Indicates regActiveKey is empty.
	if s.ID == "" {
		s.ID = TermStage
	}

	// Indicates regActiveKey doesn't exist.
	if s.ID == "0" {
		return s, nil
	}

	err = s.RetreiveTimes(RegStagesRoot, s.ID) // go/LEGACY_TYPO
	if err != nil {
		return s, err
	}

	s.State = "Running"
	if s.ID == TermStage && !s.End.IsZero() {
		s.State = "Complete"
	}

	return s, nil
}

// SetStage creates or updates the passed build stage in a database.
func SetStage(stageID string, period string) error {
	key := fmt.Sprintf(`%s\%s`, RegStagesRoot, stageID)
	time := time.Now().Format(timeFmt)
	activeValue := stageID

	if period != StartKey && period != EndKey {
		return ErrPeriod
	}

	if period == EndKey {
		activeValue = ""
	}

	if err := registry.Create(key); err != nil {
		return err
	}

	if err := registry.SetString(key, period, time); err != nil {
		return err
	}

	if err := registry.SetString(RegStagesRoot, regActiveKey, activeValue); err != nil {
		return err
	}

	return nil
}
