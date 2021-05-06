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

// Package os supports querying information about the local operating system.
package os

import (
	"errors"

	"github.com/StackExchange/wmi"
)

var (
	// ErrWMIEmptyResult indicates a condition where WMI failed to return the expected values.
	ErrWMIEmptyResult = errors.New("WMI returned without error, but zero results")
)

// Win32_OperatingSystem models the WMI object of the same name.
type Win32_OperatingSystem struct {
	ProductType int
}

// Type represents the operating system type (client or server).
type Type string

var (
	// Client represents a client operating system (eg Windows 10)
	Client Type = "client"
	// Server represents a server operating system (eg Windows Server 2019)
	Server Type = "server"
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

	if result[0].ProductType == 1 {
		return Client, nil
	}

	return Server, nil
}
