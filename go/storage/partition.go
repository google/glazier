// Copyright 2021 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License")
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

	"github.com/google/logger"
	"github.com/go-ole/go-ole"
	"github.com/go-ole/go-ole/oleutil"
)

// Partition represents a MSFT_Partition object.
//
// Ref: https://docs.microsoft.com/en-us/previous-versions/windows/desktop/stormgmt/msft-partition
type Partition struct {
	DiskNumber           int32
	PartitionNumber      int32
	DriveLetter          string
	AccessPaths          string
	OperationalStatus    int32
	TransitionState      int32
	Size                 uint64
	MbrType              int32
	GptType              string
	GUID                 string
	IsReadOnly           bool
	IsOffline            bool
	IsSystem             bool
	IsBoot               bool
	IsActive             bool
	IsHidden             bool
	IsShadowCopy         bool
	NoDefaultDriveLetter bool

	handle *ole.IDispatch
}

// Delete attempts to delete a partition.
//
// Ref: https://docs.microsoft.com/en-us/previous-versions/windows/desktop/stormgmt/msft-partition-deleteobject
func (p *Partition) Delete() error {
	var extendedStatus ole.VARIANT
	ole.VariantInit(&extendedStatus)
	resultRaw, err := oleutil.CallMethod(p.handle, "DeleteObject", &extendedStatus)
	if err != nil {
		return fmt.Errorf("DeleteObject: %w", err)
	} else if val, ok := resultRaw.Value().(int32); val != 0 || !ok {
		return fmt.Errorf("error code returned during deletion: %d", val)
	}
	return nil
}

// Resize attempts to resize a partition.
//
// Ref: https://docs.microsoft.com/en-us/previous-versions/windows/desktop/stormgmt/msft-partition-resize
func (p *Partition) Resize(size uint64) error {
	var extendedStatus ole.VARIANT
	ole.VariantInit(&extendedStatus)
	resultRaw, err := oleutil.CallMethod(p.handle, "Resize", size, &extendedStatus)
	if err != nil {
		return fmt.Errorf("Resize: %w", err)
	} else if val, ok := resultRaw.Value().(int32); val != 0 || !ok {
		return fmt.Errorf("error code returned during resize: %d", val)
	}
	return nil
}

// A PartitionSet contains one or more Partitions.
type PartitionSet struct {
	Partitions []Partition
}

// Close releases all Partition handles inside a PartitionSet.
func (s *PartitionSet) Close() {
	for _, p := range s.Partitions {
		p.handle.Release()
	}
}

// GetPartitions queries for local partitions.
//
// Close() must be called on the resulting PartitionSet to ensure all disks are released.
//
// Get all partitions:
//		svc.GetPartitions("")
//
// To get specific partitions, provide a valid WMI query filter string, for example:
//		svc.GetPartitions("WHERE DiskNumber=1")
func (svc *Service) GetPartitions(filter string) (PartitionSet, error) {
	parts := PartitionSet{}
	query := "SELECT * FROM MSFT_Partition"
	if filter != "" {
		query = fmt.Sprintf("%s %s", query, filter)
	}
	raw, err := oleutil.CallMethod(svc.wmiSvc, "ExecQuery", query)
	if err != nil {
		return parts, fmt.Errorf("ExecQuery(%s): %w", query, err)
	}
	result := raw.ToIDispatch()
	defer result.Release()

	countVar, err := oleutil.GetProperty(result, "Count")
	if err != nil {
		return parts, fmt.Errorf("oleutil.GetProperty(Count): %w", err)
	}
	count := int(countVar.Val)

	for i := 0; i < count; i++ {
		part := Partition{}
		itemRaw, err := oleutil.CallMethod(result, "ItemIndex", i)
		if err != nil {
			return parts, fmt.Errorf("oleutil.CallMethod(ItemIndex, %d): %w", i, err)
		}
		part.handle = itemRaw.ToIDispatch()

		// DriveLetter
		p, err := oleutil.GetProperty(part.handle, "DriveLetter")
		if err != nil {
			return parts, fmt.Errorf("oleutil.GetProperty(DriveLetter): %w", err)
		}
		part.DriveLetter = p.ToString()

		// DriveLetter
		p, err = oleutil.GetProperty(part.handle, "DriveLetter")
		if err != nil {
			return parts, fmt.Errorf("oleutil.GetProperty(DriveLetter): %w", err)
		}
		part.DriveLetter = p.ToString()

		// AccessPaths
		p, err = oleutil.GetProperty(part.handle, "AccessPaths")
		if err != nil {
			return parts, fmt.Errorf("oleutil.GetProperty(AccessPaths): %w", err)
		}
		part.AccessPaths = p.ToString()

		// GptType
		p, err = oleutil.GetProperty(part.handle, "GptType")
		if err != nil {
			return parts, fmt.Errorf("oleutil.GetProperty(GptType): %w", err)
		}
		part.GptType = p.ToString()

		// GUID
		p, err = oleutil.GetProperty(part.handle, "Guid")
		if err != nil {
			return parts, fmt.Errorf("oleutil.GetProperty(Guid): %w", err)
		}
		part.GUID = p.ToString()

		// All the non-strings
		for _, p := range [][]interface{}{
			[]interface{}{"DiskNumber", &part.DiskNumber},
			[]interface{}{"PartitionNumber", &part.PartitionNumber},
			[]interface{}{"OperationalStatus", &part.OperationalStatus},
			[]interface{}{"TransitionState", &part.TransitionState},
			[]interface{}{"Size", &part.Size},
			[]interface{}{"MbrType", &part.MbrType},
			[]interface{}{"IsReadOnly", &part.IsReadOnly},
			[]interface{}{"IsOffline", &part.IsOffline},
			[]interface{}{"IsSystem", &part.IsSystem},
			[]interface{}{"IsBoot", &part.IsBoot},
			[]interface{}{"IsActive", &part.IsActive},
			[]interface{}{"IsHidden", &part.IsHidden},
			[]interface{}{"IsShadowCopy", &part.IsShadowCopy},
			[]interface{}{"NoDefaultDriveLetter", &part.NoDefaultDriveLetter},
		} {
			prop, err := oleutil.GetProperty(part.handle, p[0].(string))
			if err != nil {
				return parts, fmt.Errorf("oleutil.GetProperty(%s): %w", p[0].(string), err)
			}
			if err := assignVariant(prop.Value(), p[1]); err != nil {
				logger.Warningf("assignVariant(%s): %v", p[0].(string), err)
			}
		}

		parts.Partitions = append(parts.Partitions, part)
	}

	return parts, nil
}
