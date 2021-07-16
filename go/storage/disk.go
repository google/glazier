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

package storage

import (
	"fmt"
	"reflect"
	"strconv"

	"github.com/google/logger"
	"github.com/go-ole/go-ole/oleutil"
)

// Disk represents a MSFT_Disk object.
//
// Ref: https://docs.microsoft.com/en-us/previous-versions/windows/desktop/stormgmt/msft-disk
type Disk struct {
	Path               string
	Location           string
	FriendlyName       string
	UniqueID           string
	UniqueIDFormat     int32
	Number             int32
	SerialNumber       string
	FirmwareVersion    string
	Manufacturer       string
	Model              string
	Size               uint64
	AllocatedSize      uint64
	LogicalSectorSize  int32
	PhysicalSectorSize int32
	LargestFreeExtent  uint64
	NumberOfPartitions int32
	ProvisioningType   int32
	OperationalStatus  int32
	HealthStatus       int32
	BusType            int32
	PartitionStyle     int32
	Signature          int32
	GUID               string
	IsOffline          bool
	OfflineReason      int32
	IsReadOnly         bool
	IsSystem           bool
	IsClustered        bool
	IsBoot             bool
	BootFromDisk       bool
}

// assignVariant attempts to assign an ole variant to a variable, while somewhat
// gracefully handling the various type-related shenanigans involved
func assignVariant(value interface{}, dest interface{}) error {
	// the property is nil; leave nil value in place
	srcType := reflect.TypeOf(value)
	if srcType == nil {
		return nil
	}

	dKind := reflect.TypeOf(dest).Elem().Kind()

	// avoid a panic on type mismatch
	if srcType.Kind() != dKind {
		if dKind == reflect.Uint64 && srcType.Kind() == reflect.String {
			// uint64 starts out as string
		} else {
			return fmt.Errorf("ignoring property value %v due to type mismatch (got: %v, want: %v)", value, srcType, dKind)
		}
	}

	// attempt to cast to the desired type, and assign to the variable
	switch dKind {
	case reflect.Bool:
		*dest.(*bool) = value.(bool)
	case reflect.Int32:
		*dest.(*int32) = value.(int32)
	case reflect.String:
		*dest.(*string) = value.(string)
	case reflect.Uint64:
		var err error
		if *dest.(*uint64), err = strconv.ParseUint(value.(string), 10, 64); err != nil {
			return fmt.Errorf("strconv.ParseUint(%v): %w", value, err)
		}
	default:
		return fmt.Errorf("unknown type for %v: %v", value, dKind)
	}
	return nil
}

// GetDisks queries for local disks.
//
// Get all disks:
//		svc.GetDisks("")
//
// To get specific disks, provide a valid WMI query filter string, for example:
//		svc.GetDisks("WHERE Number=1")
//		svc.GetDisks("WHERE IsSystem=True")
func (svc Service) GetDisks(filter string) ([]Disk, error) {
	disks := []Disk{}
	query := "SELECT * FROM MSFT_DISK"
	if filter != "" {
		query = fmt.Sprintf("%s %s", query, filter)
	}
	raw, err := oleutil.CallMethod(svc.wmiSvc, "ExecQuery", query)
	if err != nil {
		return disks, fmt.Errorf("ExecQuery(%s): %w", query, err)
	}
	result := raw.ToIDispatch()
	defer result.Release()

	countVar, err := oleutil.GetProperty(result, "Count")
	if err != nil {
		return disks, fmt.Errorf("oleutil.GetProperty(Count): %w", err)
	}
	count := int(countVar.Val)

	for i := 0; i < count; i++ {
		d := Disk{}
		itemRaw, err := oleutil.CallMethod(result, "ItemIndex", i)
		if err != nil {
			return disks, fmt.Errorf("oleutil.CallMethod(ItemIndex, %d): %w", i, err)
		}
		item := itemRaw.ToIDispatch()
		defer item.Release()

		// Path
		p, err := oleutil.GetProperty(item, "Path")
		if err != nil {
			return disks, fmt.Errorf("oleutil.GetProperty(Path): %w", err)
		}
		d.Path = p.ToString()

		// Location
		p, err = oleutil.GetProperty(item, "Location")
		if err != nil {
			return disks, fmt.Errorf("oleutil.GetProperty(Location): %w", err)
		}
		d.Location = p.ToString()

		// FriendlyName
		p, err = oleutil.GetProperty(item, "FriendlyName")
		if err != nil {
			return disks, fmt.Errorf("oleutil.GetProperty(FriendlyName): %w", err)
		}
		d.FriendlyName = p.ToString()

		// UniqueID
		p, err = oleutil.GetProperty(item, "UniqueId")
		if err != nil {
			return disks, fmt.Errorf("oleutil.GetProperty(UniqueId): %w", err)
		}
		d.UniqueID = p.ToString()

		// SerialNumber
		p, err = oleutil.GetProperty(item, "SerialNumber")
		if err != nil {
			return disks, fmt.Errorf("oleutil.GetProperty(SerialNumber): %w", err)
		}
		d.SerialNumber = p.ToString()

		// FirmwareVersion
		p, err = oleutil.GetProperty(item, "FirmwareVersion")
		if err != nil {
			return disks, fmt.Errorf("oleutil.GetProperty(FirmwareVersion): %w", err)
		}
		d.FirmwareVersion = p.ToString()

		// Manufacturer
		p, err = oleutil.GetProperty(item, "Manufacturer")
		if err != nil {
			return disks, fmt.Errorf("oleutil.GetProperty(Manufacturer): %w", err)
		}
		d.Manufacturer = p.ToString()

		// Model
		p, err = oleutil.GetProperty(item, "Model")
		if err != nil {
			return disks, fmt.Errorf("oleutil.GetProperty(Model): %w", err)
		}
		d.Model = p.ToString()

		// GUID
		p, err = oleutil.GetProperty(item, "Guid")
		if err != nil {
			return disks, fmt.Errorf("oleutil.GetProperty(Guid): %w", err)
		}
		d.GUID = p.ToString()

		// All the non-strings
		for _, p := range [][]interface{}{
			[]interface{}{"UniqueIdFormat", &d.UniqueIDFormat},
			[]interface{}{"Number", &d.Number},
			[]interface{}{"Size", &d.Size},
			[]interface{}{"AllocatedSize", &d.AllocatedSize},
			[]interface{}{"LogicalSectorSize", &d.LogicalSectorSize},
			[]interface{}{"PhysicalSectorSize", &d.PhysicalSectorSize},
			[]interface{}{"LargestFreeExtent", &d.LargestFreeExtent},
			[]interface{}{"NumberOfPartitions", &d.NumberOfPartitions},
			[]interface{}{"ProvisioningType", &d.ProvisioningType},
			// []interface{}{"OperationalStatus",},
			[]interface{}{"HealthStatus", &d.HealthStatus},
			[]interface{}{"BusType", &d.BusType},
			[]interface{}{"PartitionStyle", &d.PartitionStyle},
			[]interface{}{"Signature", &d.Signature},
			[]interface{}{"IsOffline", &d.IsOffline},
			[]interface{}{"OfflineReason", &d.OfflineReason},
			[]interface{}{"IsReadOnly", &d.IsReadOnly},
			[]interface{}{"IsSystem", &d.IsSystem},
			[]interface{}{"IsClustered", &d.IsClustered},
			[]interface{}{"IsBoot", &d.IsBoot},
			[]interface{}{"BootFromDisk", &d.BootFromDisk},
		} {
			prop, err := oleutil.GetProperty(item, p[0].(string))
			if err != nil {
				return disks, fmt.Errorf("oleutil.GetProperty(%s): %w", p[0].(string), err)
			}
			if err := assignVariant(prop.Value(), p[1]); err != nil {
				logger.Warningf("assignVariant(%s): %v", p[0].(string), err)
			}
		}

		disks = append(disks, d)
	}

	return disks, nil
}
