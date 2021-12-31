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
	"errors"
	"fmt"
	"strconv"

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
	AccessPaths          []string
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

// PartitionSupportedSize represents the minimum and maximum sizes a partition can be resized to.
//
// Ref: https://docs.microsoft.com/en-us/previous-versions/windows/desktop/stormgmt/msft-partition-getsupportedsizes
type PartitionSupportedSize struct {
	SizeMin uint64
	SizeMax uint64
}

// OperationalStatus describes an operational status.
//
// Ref: https://docs.microsoft.com/en-us/previous-versions/windows/desktop/stormgmt/msft-partition
type OperationalStatus uint16

const (
	// UnknownOperationalStatus is a type of Operational Status
	UnknownOperationalStatus OperationalStatus = 0
	// OnlineOperationalStatus is a type of Operational Status
	OnlineOperationalStatus OperationalStatus = 1
	// NoMediaOperationalStatus is a type of Operational Status
	NoMediaOperationalStatus OperationalStatus = 3
	// FailedOperationalStatus is a type of Operational Status
	FailedOperationalStatus OperationalStatus = 5
	// OfflineOperationalStatus is a type of Operational Status
	OfflineOperationalStatus OperationalStatus = 4
)

// Close releases the handle to the partition.
func (p *Partition) Close() {
	if p.handle != nil {
		p.handle.Release()
	}
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

// Offline takes the partition offline.
//
// Example:
//		p.Offline()
//
// Ref: https://docs.microsoft.com/en-us/previous-versions/windows/desktop/stormgmt/msft-partition-offline
func (p *Partition) Offline() (ExtendedStatus, error) {
	stat := ExtendedStatus{}
	var extendedStatus ole.VARIANT
	ole.VariantInit(&extendedStatus)
	res, err := oleutil.CallMethod(p.handle, "Offline", &extendedStatus)
	if err != nil {
		return stat, fmt.Errorf("Offline(): %w", err)
	} else if val, ok := res.Value().(int32); val != 0 || !ok {
		return stat, fmt.Errorf("error code returned during offline: %d", val)
	}
	return stat, nil
}

// Online brings the partition online by mounting the associated volume (if one exists).
//
// Example:
//		p.Online()
//
// Ref: https://docs.microsoft.com/en-us/previous-versions/windows/desktop/stormgmt/msft-partition-online
func (p *Partition) Online() (ExtendedStatus, error) {
	stat := ExtendedStatus{}
	var extendedStatus ole.VARIANT
	ole.VariantInit(&extendedStatus)
	res, err := oleutil.CallMethod(p.handle, "Online", &extendedStatus)
	if err != nil {
		return stat, fmt.Errorf("Online(): %w", err)
	} else if val, ok := res.Value().(int32); val != 0 || !ok {
		return stat, fmt.Errorf("error code returned during online: %d", val)
	}
	return stat, nil
}

// AddAccessPath adds a mount path or drive letter assignment to the partition.
//
// Example: assign a Drive letter with D:
//		p.AddAccessPath("D:", false)
//
// Example: Automatically assign the next available Drive Letter:
//		p.AddAccessPath("", true)
//
// Note: You cannot specify both a valid drive letter and auto assignment as true together.
//
// Ref: https://docs.microsoft.com/en-us/previous-versions/windows/desktop/stormgmt/addaccesspath-msft-partition
func (p *Partition) AddAccessPath(accessPath string, autoAssign bool) (ExtendedStatus, error) {
	stat := ExtendedStatus{}
	var extendedStatus ole.VARIANT
	ole.VariantInit(&extendedStatus)
	var resultRaw *ole.VARIANT
	var err error
	if autoAssign {
		resultRaw, err = oleutil.CallMethod(p.handle, "AddAccessPath", nil, autoAssign, &extendedStatus)
	} else {
		resultRaw, err = oleutil.CallMethod(p.handle, "AddAccessPath", accessPath, nil, &extendedStatus)
	}
	if err != nil {
		return stat, fmt.Errorf("AddAccessPath: %w", err)
	} else if val, ok := resultRaw.Value().(int32); val != 0 || !ok {
		return stat, fmt.Errorf("error code returned during AddAccessPath: %d", val)
	}
	return stat, nil
}

// RemoveAccessPath removes the access path from the partition.
//
// Example: Remove the driveLetter of D: from a partition
//		p.RemoveAccessPath("D:")
//
// Ref: https://docs.microsoft.com/en-us/previous-versions/windows/desktop/stormgmt/removeaccesspath-msft-partition
func (p *Partition) RemoveAccessPath(accessPath string) (ExtendedStatus, error) {
	stat := ExtendedStatus{}
	var extendedStatus ole.VARIANT
	ole.VariantInit(&extendedStatus)
	resultRaw, err := oleutil.CallMethod(p.handle, "RemoveAccessPath", accessPath, &extendedStatus)
	if err != nil {
		return stat, fmt.Errorf("RemoveAccessPath: %w", err)
	} else if val, ok := resultRaw.Value().(int32); val != 0 || !ok {
		return stat, fmt.Errorf("error code returned during RemoveAccessPath: %d", val)
	}
	return stat, nil
}

// Query reads and populates the partition state.
func (p *Partition) Query() error {
	if p.handle == nil {
		return fmt.Errorf("invalid handle")
	}

	// DriveLetter
	prop, err := oleutil.GetProperty(p.handle, "DriveLetter")
	if err != nil {
		return fmt.Errorf("oleutil.GetProperty(DriveLetter): %w", err)
	}
	// DriveLetter is represented as Char16 (Ascii)
	if prop.Val != 0 { // leave NUL as empty string
		p.DriveLetter = string(rune(prop.Val))
	}

	// AccessPaths
	prop, err = oleutil.GetProperty(p.handle, "AccessPaths")
	if err != nil {
		return fmt.Errorf("oleutil.GetProperty(AccessPaths): %w", err)
	}

	if prop.Val != 0 { // leave NUL as empty string
		for _, pa := range prop.ToArray().ToValueArray() {
			conv, ok := pa.(string)
			if !ok {
				return errors.New("error converting access path")
			}
			p.AccessPaths = append(p.AccessPaths, conv)
		}
	}

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
	// Convert the unint to a string because of because of https://docs.microsoft.com/en-us/previous-versions//aa393262%28v=vs.85%29?redirectedfrom=MSDN
	resultRaw, err := oleutil.CallMethod(p.handle, "Resize", strconv.FormatUint(size, 10), &extendedStatus)
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

// GetSupportedSize retrieves the minimum and maximum sizes that the partition can be resized to
//
// Ref: https://docs.microsoft.com/en-us/previous-versions/windows/desktop/stormgmt/msft-partition-getsupportedsizes
func (p *Partition) GetSupportedSize() (PartitionSupportedSize, ExtendedStatus, error) {
	size := PartitionSupportedSize{}
	stat := ExtendedStatus{}

	var sizemin ole.VARIANT
	ole.VariantInit(&sizemin)
	var sizemax ole.VARIANT
	ole.VariantInit(&sizemax)
	var extendedstatus ole.VARIANT
	ole.VariantInit(&extendedstatus)

	resultRaw, err := oleutil.CallMethod(p.handle, "GetSupportedSize", &sizemin, &sizemax, &extendedstatus)
	if err != nil {
		return size, stat, fmt.Errorf("GetSupportedSize: %w", err)
	} else if val, ok := resultRaw.Value().(int32); val != 0 || !ok {
		return size, stat, fmt.Errorf("error code returned during GetSupportedSize: %d", val)
	}

	// Convert the results from an interface to uint64
	// Results are returned as strings because of https://docs.microsoft.com/en-us/previous-versions//aa393262%28v=vs.85%29?redirectedfrom=MSDN
	size.SizeMin, err = strconv.ParseUint(sizemin.Value().(string), 10, 64)
	if err != nil {
		return size, stat, fmt.Errorf("error attempting to parse sizemin: %w", err)
	}
	size.SizeMax, err = strconv.ParseUint(sizemax.Value().(string), 10, 64)
	if err != nil {
		return size, stat, fmt.Errorf("error attempting to parse sizemax: %w", err)
	}
	return size, stat, nil
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
