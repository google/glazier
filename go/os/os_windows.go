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

// Package os supports querying information about the local operating system.
package os

import (
	"github.com/StackExchange/wmi"
)

// GetType attempts to distinguish between client and server OS.
func GetType() (Type, error) {
	var result []Win32_OperatingSystem
	if err := wmi.Query(wmi.CreateQuery(&result, ""), &result); err != nil {
		return Server, err
	}
	if len(result) < 1 {
		return Server, ErrWMIEmptyResult
	}

	switch result[0].ProductType {
	case 1:
		return Client, nil
	case 2:
		return DomainController, nil
	case 3:
		return Server, nil
	default:
		return Unknown, nil
	}
}
