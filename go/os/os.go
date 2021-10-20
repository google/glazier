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

package os

import "errors"

var (
	// ErrWMIEmptyResult indicates a condition where WMI failed to return the expected values.
	ErrWMIEmptyResult = errors.New("WMI returned without error, but zero results")
	// ErrNotImplemented is returned for unimplemented calls
	ErrNotImplemented = errors.New("call is not implemented on this platform")
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
	// DomainController represents a server operating system acting as a domain controller
	DomainController Type = "domain controller"
	// Server represents a server operating system (eg Windows Server 2019)
	Server Type = "server"
	// Unknown represents an unsupported type
	Unknown Type = "unknown"
)
