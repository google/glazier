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

// +build windows

// Package identity provides helpers for managing host identity.
package identity

import (
	"errors"
	"strings"

	"github.com/google/uuid"
	"github.com/StackExchange/wmi"
)

type Win32_ComputerSystem struct {
	Partofdomain bool
}

// DomainJoined attempts to determine whether the machine is actively domain joined.
func DomainJoined() (bool, error) {
	var c []Win32_ComputerSystem
	q := wmi.CreateQuery(&c, "")

	if err := wmi.Query(q, &c); err != nil {
		return false, err
	}
	if len(c) < 1 {
		return false, errors.New("no result from wmi query")
	}
	return c[0].Partofdomain, nil
}

// ImageID generates a Glazier unique Image ID.
// Serial should be the device serial number, as reported by the BIOS.
func ImageID(serial string) string {
	u := strings.ToUpper(uuid.NewString())
	return strings.ToUpper(serial) + "-" + u[len(u)-7:]
}
