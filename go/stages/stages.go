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
	"strconv"

	"golang.org/x/sys/windows/registry"
)

const (
	regStagesRoot = `SOFTWARE\Glazier\Stages`
	regActiveKey  = "_Active"
)

func getActiveStage(root string) (uint64, error) {
	k, err := registry.OpenKey(registry.LOCAL_MACHINE, root, registry.QUERY_VALUE)
	if err != nil {
		if err == registry.ErrNotExist {
			return 0, nil
		}
		return 0, err
	}
	defer k.Close()

	active, _, err := k.GetStringValue(regActiveKey)
	if err != nil {
		if err == registry.ErrNotExist {
			return 0, nil
		}
		return 0, err
	}
	return strconv.ParseUint(active, 10, 64)
}

// GetActiveStage returns the active build stage for the machine.
func GetActiveStage() (uint64, error) {
	// TODO: Implement stage expiration here
	return getActiveStage(regStagesRoot)
}
