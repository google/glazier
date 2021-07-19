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

// Volume represents a MSFT_Volume object.
//
// Ref: https://docs.microsoft.com/en-us/previous-versions/windows/desktop/stormgmt/msft-volume
type Volume struct {
	DriveLetter     string
	Path            string
	HealthStatus    uint16
	FileSystem      string
	FileSystemLabel string
	FileSystemType  uint16
	Size            uint64
	SizeRemaining   uint64
	DriveType       uint32
	DedupMode       uint32

	handle *ole.IDispatch
}

// Format formats a volume.
//
// fs can be one of "ExFAT", "FAT", "FAT32", "NTFS", "ReFS"
//
// Ref: https://docs.microsoft.com/en-us/previous-versions/windows/desktop/stormgmt/format-msft-volume
func (v *Volume) Format(fs string, fsLabel string, allocationUnitSize int,
	full, force, compress, shortFileNameSupport, setIntegrityStreams, useLargeFRS, disableHeatGathering bool) error {

	var extendedStatus ole.VARIANT
	ole.VariantInit(&extendedStatus)
	var formattedVolume ole.VARIANT
	ole.VariantInit(&formattedVolume)

	res, err := oleutil.CallMethod(v.handle, "Format", fs, fsLabel, allocationUnitSize, full, force, compress,
		shortFileNameSupport, setIntegrityStreams, useLargeFRS, disableHeatGathering, &formattedVolume, &extendedStatus)
	if err != nil {
		return fmt.Errorf("Format: %w", err)
	} else if val, ok := res.Value().(int32); val != 0 || !ok {
		return fmt.Errorf("error code returned during formatting: %d", val)
	}
	return nil
}

// A VolumeSet contains one or more Volumes.
type VolumeSet struct {
	Volumes []Volume
}

// Close releases all Volume handles inside a VolumeSet.
func (s *VolumeSet) Close() {
	for _, v := range s.Volumes {
		v.handle.Release()
	}
}

// GetVolumes queries for local volumes.
//
// Close() must be called on the resulting VolumeSet to ensure all volumes are released.
//
// Get all volumes:
//		svc.GetVolumes("")
//
// To get specific volumes, provide a valid WMI query filter string, for example:
//		svc.GetVolumes("WHERE DriveLetter=D")
func (svc Service) GetVolumes(filter string) (VolumeSet, error) {
	vset := VolumeSet{}
	query := "SELECT * FROM MSFT_Volume"
	if filter != "" {
		query = fmt.Sprintf("%s %s", query, filter)
	}
	raw, err := oleutil.CallMethod(svc.wmiSvc, "ExecQuery", query)
	if err != nil {
		return vset, fmt.Errorf("ExecQuery(%s): %w", query, err)
	}
	result := raw.ToIDispatch()
	defer result.Release()

	countVar, err := oleutil.GetProperty(result, "Count")
	if err != nil {
		return vset, fmt.Errorf("oleutil.GetProperty(Count): %w", err)
	}
	count := int(countVar.Val)

	for i := 0; i < count; i++ {
		v := Volume{}
		itemRaw, err := oleutil.CallMethod(result, "ItemIndex", i)
		if err != nil {
			return vset, fmt.Errorf("oleutil.CallMethod(ItemIndex, %d): %w", i, err)
		}
		v.handle = itemRaw.ToIDispatch()

		// DriveLetter
		p, err := oleutil.GetProperty(v.handle, "DriveLetter")
		if err != nil {
			return vset, fmt.Errorf("oleutil.GetProperty(DriveLetter): %w", err)
		}
		// DriveLetter is represented as Char16 (Ascii)
		v.DriveLetter = string(rune(p.Val))

		// Path
		p, err = oleutil.GetProperty(v.handle, "Path")
		if err != nil {
			return vset, fmt.Errorf("oleutil.GetProperty(Path): %w", err)
		}
		v.Path = p.ToString()

		// FileSystem
		p, err = oleutil.GetProperty(v.handle, "FileSystem")
		if err != nil {
			return vset, fmt.Errorf("oleutil.GetProperty(FileSystem): %w", err)
		}
		v.FileSystem = p.ToString()

		// FileSystemLabel
		p, err = oleutil.GetProperty(v.handle, "FileSystemLabel")
		if err != nil {
			return vset, fmt.Errorf("oleutil.GetProperty(FileSystemLabel): %w", err)
		}
		v.FileSystemLabel = p.ToString()

		// All the non-strings
		for _, p := range [][]interface{}{
			[]interface{}{"HealthStatus", &v.HealthStatus},
			[]interface{}{"FileSystemType", &v.FileSystemType},
			[]interface{}{"Size", &v.Size},
			[]interface{}{"SizeRemaining", &v.SizeRemaining},
			[]interface{}{"DriveType", &v.DriveType},
			[]interface{}{"DedupMode", &v.DedupMode},
		} {
			prop, err := oleutil.GetProperty(v.handle, p[0].(string))
			if err != nil {
				return vset, fmt.Errorf("oleutil.GetProperty(%s): %w", p[0].(string), err)
			}
			if err := assignVariant(prop.Value(), p[1]); err != nil {
				logger.Warningf("assignVariant(%s): %v", p[0].(string), err)
			}
		}

		vset.Volumes = append(vset.Volumes, v)
	}

	return vset, nil
}
