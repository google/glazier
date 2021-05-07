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

// +build windows

// Package stages allows interacting with Glazier build stages.
package stages

import (
	"fmt"
	"strconv"
	"time"

	"github.com/google/glazier/go/registry"
)

const (
	defaultTimeout = 60 * 24 * 7 * time.Minute // 7 days
	regStagesRoot  = `SOFTWARE\Glazier\Stages`
	regActiveKey   = "_Active"
	term           = "100" // Stage after which to consider the build completed
)

var (
	err error
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

func getActiveTime(root, stageID string, period string) (time.Time, error) {
	switch period {
	case "Start", "End":
		active, err := registry.GetString(fmt.Sprintf(`%s\%s`, root, stageID), period)
		if err != nil && err != registry.ErrNotExist {
			return time.Time{}, err
		}

		var at time.Time
		if active != "" {
			at, err = time.Parse("2006-01-02T15:04:05.000000", active)
			if err != nil {
				return time.Time{}, err
			}
		}
		return at, nil
	default:
		return time.Time{}, fmt.Errorf("unsupported period passed to getActiveTime: %q", period)
	}

}

// GetTimes return the start and end time of a build stage.
func GetTimes(root, stageID string) (time.Time, time.Time, error) {
	stage := NewStage()

	if stage.Start, err = getActiveTime(root, stageID, "Start"); err != nil {
		return stage.Start, stage.End, err
	}

	if stage.End, err = getActiveTime(root, stageID, "End"); err != nil {
		return stage.Start, stage.End, err
	}

	return stage.Start, stage.End, nil
}

func checkExpiration(stageID string) error {
	// TODO: Implement stage expiration here
	_, _, err := GetTimes(regStagesRoot, stageID)
	return err
}

func getActiveStage(root string) (string, error) {
	active, err := registry.GetString(root, regActiveKey)
	if err != nil {
		if err != registry.ErrNotExist {
			return "", err
		}
		return "0", nil
	}
	return active, nil
}

// GetActiveStage returns the active build stage for the machine.
func GetActiveStage() (uint64, error) {
	stage, err := getActiveStage(regStagesRoot)
	if err != nil {
		return 0, err
	}
	err = checkExpiration(stage)
	if err != nil {
		return 0, err
	}

	return strconv.ParseUint(stage, 10, 64)
}

// GetStage obtains the active stage timers and stage.
func GetStage() (*Stage, error) {
	stage := NewStage()

	stage.ID, err = getActiveStage(regStagesRoot)
	if err != nil {
		return stage, err
	}
	if stage.ID == "" {
		stage.ID = term
	}

	stage.Start, stage.End, err = GetTimes(regStagesRoot, stage.ID)
	if err != nil {
		return stage, err
	}

	if stage.ID == term && !stage.End.IsZero() {
		stage.State = "Complete"
	} else {
		stage.State = "Running"
	}

	return stage, nil
}
