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
}

// GetPartitions queries for local partitions.
//
// Get all partitions:
//		svc.GetPartitions("")
//
// To get specific partitions, provide a valid WMI query filter string, for example:
//		svc.GetPartitions("WHERE DiskNumber=1")
func (svc Service) GetPartitions(filter string) ([]Partition, error) {
	parts := []Partition{}
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
		item := itemRaw.ToIDispatch()
		defer item.Release()

		// DriveLetter
		p, err := oleutil.GetProperty(item, "DriveLetter")
		if err != nil {
			return parts, fmt.Errorf("oleutil.GetProperty(DriveLetter): %w", err)
		}
		part.DriveLetter = p.ToString()

		// DriveLetter
		p, err = oleutil.GetProperty(item, "DriveLetter")
		if err != nil {
			return parts, fmt.Errorf("oleutil.GetProperty(DriveLetter): %w", err)
		}
		part.DriveLetter = p.ToString()

		// AccessPaths
		p, err = oleutil.GetProperty(item, "AccessPaths")
		if err != nil {
			return parts, fmt.Errorf("oleutil.GetProperty(AccessPaths): %w", err)
		}
		part.AccessPaths = p.ToString()

		// GptType
		p, err = oleutil.GetProperty(item, "GptType")
		if err != nil {
			return parts, fmt.Errorf("oleutil.GetProperty(GptType): %w", err)
		}
		part.GptType = p.ToString()

		// GUID
		p, err = oleutil.GetProperty(item, "Guid")
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
			prop, err := oleutil.GetProperty(item, p[0].(string))
			if err != nil {
				return parts, fmt.Errorf("oleutil.GetProperty(%s): %w", p[0].(string), err)
			}
			if err := assignVariant(prop.Value(), p[1]); err != nil {
				logger.Warningf("assignVariant(%s): %v", p[0].(string), err)
			}
		}

		parts = append(parts, part)
	}

	return parts, nil
}
