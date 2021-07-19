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

// Close releases the handle to the partition.
func (p *Partition) Close() {
	p.handle.Release()
}

// Delete attempts to delete a partition.
//
// Ref: https://docs.microsoft.com/en-us/previous-versions/windows/desktop/stormgmt/msft-partition-deleteobject
func (p *Partition) Delete() (ExtendedStatus, error) {
	stat := ExtendedStatus{}
	var extendedStatus ole.VARIANT
	ole.VariantInit(&extendedStatus)
	resultRaw, err := oleutil.CallMethod(p.handle, "DeleteObject", &extendedStatus)
	if err != nil {
		return stat, fmt.Errorf("DeleteObject: %w", err)
	} else if val, ok := resultRaw.Value().(int32); val != 0 || !ok {
		return stat, fmt.Errorf("error code returned during deletion: %d", val)
	}
	return stat, nil
}

// Query reads and populates the partition state.
func (p *Partition) Query() error {
	// DriveLetter
	prop, err := oleutil.GetProperty(p.handle, "DriveLetter")
	if err != nil {
		return fmt.Errorf("oleutil.GetProperty(DriveLetter): %w", err)
	}
	// DriveLetter is represented as Char16 (Ascii)
	p.DriveLetter = string(rune(prop.Val))

	// AccessPaths
	prop, err = oleutil.GetProperty(p.handle, "AccessPaths")
	if err != nil {
		return fmt.Errorf("oleutil.GetProperty(AccessPaths): %w", err)
	}
	p.AccessPaths = prop.ToString()

	// GptType
	prop, err = oleutil.GetProperty(p.handle, "GptType")
	if err != nil {
		return fmt.Errorf("oleutil.GetProperty(GptType): %w", err)
	}
	p.GptType = prop.ToString()

	// GUID
	prop, err = oleutil.GetProperty(p.handle, "Guid")
	if err != nil {
		return fmt.Errorf("oleutil.GetProperty(Guid): %w", err)
	}
	p.GUID = prop.ToString()

	// All the non-strings
	for _, prop := range [][]interface{}{
		[]interface{}{"DiskNumber", &p.DiskNumber},
		[]interface{}{"PartitionNumber", &p.PartitionNumber},
		[]interface{}{"OperationalStatus", &p.OperationalStatus},
		[]interface{}{"TransitionState", &p.TransitionState},
		[]interface{}{"Size", &p.Size},
		[]interface{}{"MbrType", &p.MbrType},
		[]interface{}{"IsReadOnly", &p.IsReadOnly},
		[]interface{}{"IsOffline", &p.IsOffline},
		[]interface{}{"IsSystem", &p.IsSystem},
		[]interface{}{"IsBoot", &p.IsBoot},
		[]interface{}{"IsActive", &p.IsActive},
		[]interface{}{"IsHidden", &p.IsHidden},
		[]interface{}{"IsShadowCopy", &p.IsShadowCopy},
		[]interface{}{"NoDefaultDriveLetter", &p.NoDefaultDriveLetter},
	} {
		val, err := oleutil.GetProperty(p.handle, prop[0].(string))
		if err != nil {
			return fmt.Errorf("oleutil.GetProperty(%s): %w", prop[0].(string), err)
		}
		if err := assignVariant(val.Value(), prop[1]); err != nil {
			logger.Warningf("assignVariant(%s): %v", prop[0].(string), err)
		}
	}
	return nil
}

// Resize attempts to resize a partition.
//
// Ref: https://docs.microsoft.com/en-us/previous-versions/windows/desktop/stormgmt/msft-partition-resize
func (p *Partition) Resize(size uint64) (ExtendedStatus, error) {
	stat := ExtendedStatus{}
	var extendedStatus ole.VARIANT
	ole.VariantInit(&extendedStatus)
	resultRaw, err := oleutil.CallMethod(p.handle, "Resize", size, &extendedStatus)
	if err != nil {
		return stat, fmt.Errorf("Resize: %w", err)
	} else if val, ok := resultRaw.Value().(int32); val != 0 || !ok {
		return stat, fmt.Errorf("error code returned during resize: %d", val)
	}
	return stat, nil
}

// A PartitionSet contains one or more Partitions.
type PartitionSet struct {
	Partitions []Partition
}

// Close releases all Partition handles inside a PartitionSet.
func (s *PartitionSet) Close() {
	for _, p := range s.Partitions {
		p.Close()
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

		if err := part.Query(); err != nil {
			return parts, err
		}

		parts.Partitions = append(parts.Partitions, part)
	}

	return parts, nil
}
