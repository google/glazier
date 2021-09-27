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
	HealthStatus    int32
	FileSystem      string
	FileSystemLabel string
	FileSystemType  int32
	Size            uint64
	SizeRemaining   uint64
	DriveType       int32
	DedupMode       int32

	handle *ole.IDispatch
}

// Close releases the handle to the volume.
func (v *Volume) Close() {
	if v.handle != nil {
		v.handle.Release()
	}
}

// Flush flushes the cached data in the volume's file system to disk.
//
// Ref: https://docs.microsoft.com/en-us/previous-versions/windows/desktop/stormgmt/msft-volume-flush
func (v *Volume) Flush() error {
	res, err := oleutil.CallMethod(v.handle, "Flush")
	if err != nil {
		return fmt.Errorf("Flush: %w", err)
	} else if val, ok := res.Value().(int32); val != 0 || !ok {
		return fmt.Errorf("error code returned during flush: %d", val)
	}
	return nil
}

// FormatFAT32 is a helper for calling Format using only the options supported by FAT32.
func (v *Volume) FormatFAT32(label string, allocationUnitSize int32, full, force bool) (Volume, ExtendedStatus, error) {
	return v.Format("FAT32", label, allocationUnitSize, full, force, nil, nil, nil, nil, nil)
}

// FormatNTFS is a helper for calling Format using only the options supported by NTFS.
func (v *Volume) FormatNTFS(label string, allocationUnitSize int32, full, force, compress, shortFileNameSupport, useLargeFRS, disableHeatGathering bool) (Volume, ExtendedStatus, error) {
	return v.Format("NTFS", label, allocationUnitSize, full, force, compress, shortFileNameSupport, nil, useLargeFRS, disableHeatGathering)
}

// FormatReFS is a helper for calling Format using only the options supported by ReFS.
func (v *Volume) FormatReFS(label string, allocationUnitSize int32, full, force, setIntegrityStreams, disableHeatGathering bool) (Volume, ExtendedStatus, error) {
	return v.Format("ReFS", label, allocationUnitSize, full, force, nil, nil, setIntegrityStreams, nil, disableHeatGathering)
}

// Format formats a volume.
//
// You may want to use one of the filesystem-specific helpers instead of calling this directly.
//
// fs can be one of "ExFAT", "FAT", "FAT32", "NTFS", "ReFS". Set allocationUnitSize to 0 for default.
//
// Note: The Windows API requires any parameters not supported by a given filesystem to be nil (NOT zero value).
// To enable this here, any non-universal parameters are implemented as interfaces and must be passed as either the
// correct type for the underlying API field or nil. Attempting to pass a field to a filesystem that doesn't
// support it will result in a vague and unhelpful code 1 (unsupported) from the API.
//
// If successful, the formatted volume is returned as a new Volume object. Close() must be called on the new Volume.
//
// Ref: https://docs.microsoft.com/en-us/previous-versions/windows/desktop/stormgmt/format-msft-volume
func (v *Volume) Format(
	fs string,
	fsLabel string,
	allocationUnitSize int32,
	full bool,
	force bool,
	compress interface{},
	shortFileNameSupport interface{},
	setIntegrityStreams interface{},
	useLargeFRS interface{},
	disableHeatGathering interface{}) (Volume, ExtendedStatus, error) {
	vol := Volume{}
	stat := ExtendedStatus{}

	var extendedStatus ole.VARIANT
	ole.VariantInit(&extendedStatus)
	var formattedVolume ole.VARIANT
	ole.VariantInit(&formattedVolume)

	var ialloc interface{}
	if allocationUnitSize != 0 {
		ialloc = allocationUnitSize
	} else {
		ialloc = nil
	}

	res, err := oleutil.CallMethod(v.handle, "Format",
		fs,
		fsLabel,
		ialloc,
		full,
		force,
		compress,
		shortFileNameSupport,
		setIntegrityStreams,
		useLargeFRS,
		disableHeatGathering,
		&formattedVolume, &extendedStatus) // outputs
	if err != nil {
		return vol, stat, fmt.Errorf("Format: %w", err)
	} else if val, ok := res.Value().(int32); val != 0 || !ok {
		return vol, stat, fmt.Errorf("error code returned during formatting: %d", val)
	}

	// TODO(mattl): figure out why this handle is invalid
	vol.handle = formattedVolume.ToIDispatch()

	return vol, stat, nil
}

// Optimize optimizes the volume.
//
// Ref: https://docs.microsoft.com/en-us/previous-versions/windows/desktop/stormgmt/optimize-msft-volume
func (v *Volume) Optimize(reTrim, analyze, defrag, slabConslidate, tierOptimize bool) (ExtendedStatus, error) {
	stat := ExtendedStatus{}
	var extendedStatus ole.VARIANT
	ole.VariantInit(&extendedStatus)

	res, err := oleutil.CallMethod(v.handle, "Optimize", reTrim, analyze, defrag, slabConslidate, tierOptimize, &extendedStatus)
	if err != nil {
		return stat, fmt.Errorf("Optimize: %w", err)
	} else if val, ok := res.Value().(int32); val != 0 || !ok {
		return stat, fmt.Errorf("error code returned during optimization: %d", val)
	}
	return stat, nil
}

// SetFileSystemLabel Sets the file system label for the volume.
//
// Ref: https://docs.microsoft.com/en-us/previous-versions/windows/desktop/stormgmt/msft-volume-setfilesystemlabel
func (v *Volume) SetFileSystemLabel(fileSystemLabel string) (ExtendedStatus, error) {
	stat := ExtendedStatus{}
	var extendedStatus ole.VARIANT
	ole.VariantInit(&extendedStatus)

	res, err := oleutil.CallMethod(v.handle, "SetFileSystemLabel", fileSystemLabel, &extendedStatus)
	if err != nil {
		return stat, fmt.Errorf("SetFileSystemLabel: %w", err)
	} else if val, ok := res.Value().(int32); val != 0 || !ok {
		return stat, fmt.Errorf("error code returned during setting file system label: %d", val)
	}
	return stat, nil
}

// Query reads and populates the volume state.
func (v *Volume) Query() error {
	if v.handle == nil {
		return fmt.Errorf("invalid handle")
	}

	// DriveLetter
	p, err := oleutil.GetProperty(v.handle, "DriveLetter")
	if err != nil {
		return fmt.Errorf("oleutil.GetProperty(DriveLetter): %w", err)
	}
	// DriveLetter is represented as Char16 (Ascii)
	v.DriveLetter = string(rune(p.Val))

	// Path
	p, err = oleutil.GetProperty(v.handle, "Path")
	if err != nil {
		return fmt.Errorf("oleutil.GetProperty(Path): %w", err)
	}
	v.Path = p.ToString()

	// FileSystem
	p, err = oleutil.GetProperty(v.handle, "FileSystem")
	if err != nil {
		return fmt.Errorf("oleutil.GetProperty(FileSystem): %w", err)
	}
	v.FileSystem = p.ToString()

	// FileSystemLabel
	p, err = oleutil.GetProperty(v.handle, "FileSystemLabel")
	if err != nil {
		return fmt.Errorf("oleutil.GetProperty(FileSystemLabel): %w", err)
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
			return fmt.Errorf("oleutil.GetProperty(%s): %w", p[0].(string), err)
		}
		if err := assignVariant(prop.Value(), p[1]); err != nil {
			logger.Warningf("assignVariant(%s): %v", p[0].(string), err)
		}
	}
	return nil
}

// DriveType describes a Drive Type
//
// Ref: https://docs.microsoft.com/en-us/previous-versions/windows/desktop/stormgmt/msft-volume
type DriveType int

const (
	// UnknownDriveType is a type of Drive Type
	UnknownDriveType DriveType = iota
	// Invalid is a type of Drive Type
	Invalid
	// Removable is a type of Drive Type
	Removable
	// Fixed is a type of Drive Type
	Fixed
	// Remote is a type of Drive Type
	Remote
	// CDROM is a type of Drive Type
	CDROM
	// RAM is a type of Drive Type
	RAM
)

// A VolumeSet contains one or more Volumes.
type VolumeSet struct {
	Volumes []Volume
}

// Close releases all Volume handles inside a VolumeSet.
func (s *VolumeSet) Close() {
	for _, v := range s.Volumes {
		v.Close()
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

	logger.V(1).Info(query)
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

		if err := v.Query(); err != nil {
			return vset, err
		}

		vset.Volumes = append(vset.Volumes, v)
	}

	return vset, nil
}
