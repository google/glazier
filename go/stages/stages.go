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

	"golang.org/x/sys/windows/registry"
)

const (
	defaultTimeout = 60 * 24 * 7 * time.Minute // 7 days
	regStagesRoot  = `SOFTWARE\Glazier\Stages`
	regActiveKey   = "_Active"
)

func checkExpiration(stageID string) error {
	// TODO: Implement stage expiration here
	_, err := getActiveTime(regStagesRoot, stageID)
	return err
}

func getActiveStage(root string) (string, error) {
	active, err := readKey(root, regActiveKey)
	if err != nil {
		if err != registry.ErrNotExist {
			return "", err
		}
		return "0", nil
	}
	return active, nil
}

func getActiveTime(root, stageID string) (time.Time, error) {
	active, err := readKey(fmt.Sprintf(`%s\%s`, root, stageID), "Start")
	if err != nil {
		return time.Time{}, err
	}
	return time.Parse("2006-01-02T15:04:05.000000", active)
}

func readKey(root, key string) (string, error) {
	k, err := registry.OpenKey(registry.LOCAL_MACHINE, root, registry.QUERY_VALUE)
	if err != nil {
		return "", err
	}
	defer k.Close()

	active, _, err := k.GetStringValue(key)
	return active, err
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
