// Copyright 2025 Google LLC
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

// Package netw provides network adapter management functionality.
package netw

import (
	"fmt"
	"strconv"

	"github.com/scjalliance/comshim"
	"github.com/go-ole/go-ole"
	"github.com/go-ole/go-ole/oleutil"
)

// Connect connects to the WMI provider for managing storage objects.
// You must call Close() to release the provider when finished.
//
// Example: storage.Connect()
func Connect() (Service, error) {
	comshim.Add(1)
	svc := Service{}

	unknown, err := oleutil.CreateObject("WbemScripting.SWbemLocator")
	if err != nil {
		comshim.Done()
		return svc, fmt.Errorf("CreateObject: %w", err)
	}
	defer unknown.Release()
	svc.wmiIntf, err = unknown.QueryInterface(ole.IID_IDispatch)
	if err != nil {
		comshim.Done()
		return svc, fmt.Errorf("QueryInterface: %w", err)
	}
	serviceRaw, err := oleutil.CallMethod(svc.wmiIntf, "ConnectServer", nil, `\\.\ROOT\StandardCimv2`)
	if err != nil {
		svc.Close()
		return svc, fmt.Errorf("ConnectServer: %w", err)
	}
	svc.wmiSvc = serviceRaw.ToIDispatch()

	return svc, nil
}

// Close frees all resources associated with a volume.
func (svc *Service) Close() {
	svc.wmiIntf.Release()
	if svc.wmiSvc != nil {
		svc.wmiSvc.Release()
	}
	comshim.Done()
}

// AssignVariant assigns a variant to a destination.
func AssignVariant(v any, dst any) error {
	switch d := dst.(type) {
	case *bool:
		b, ok := v.(bool)
		if !ok {
			return fmt.Errorf("cannot assign %T to *bool", v)
		}
		*d = b
	case *uint8:
		switch val := v.(type) {
		case uint8:
			*d = val
		case int16:
			*d = uint8(val)
		case int32:
			*d = uint8(val)
		default:
			return fmt.Errorf("cannot assign %T to *uint8", v)
		}
	case *uint16:
		i, ok := v.(int32)
		if !ok {
			i16, ok16 := v.(int16)
			if !ok16 {
				return fmt.Errorf("cannot assign %T to *uint16", v)
			}
			i = int32(i16)
		}
		*d = uint16(i)
	case *uint32:
		i, ok := v.(int32)
		if !ok {
			return fmt.Errorf("cannot assign %T to *uint32", v)
		}
		*d = uint32(i)
	case *uint64:
		s, ok := v.(string)
		if ok {
			parsed, err := strconv.ParseUint(s, 10, 64)
			if err != nil {
				return fmt.Errorf("cannot parse uint64 from string '%s': %w", s, err)
			}
			*d = parsed
			return nil
		}
		i, ok := v.(int64)
		if !ok {
			i32, ok32 := v.(int32)
			if !ok32 {
				return fmt.Errorf("cannot assign %T to *uint64", v)
			}
			i = int64(i32)
		}
		*d = uint64(i)
	default:
		return fmt.Errorf("unsupported destination type %T", dst)
	}
	return nil
}
