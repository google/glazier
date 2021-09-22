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
	"github.com/go-ole/go-ole"
	"github.com/go-ole/go-ole/oleutil"
)

// BusType describes a Bus Type
//
// Ref: https://docs.microsoft.com/en-us/previous-versions/windows/desktop/stormgmt/msft-disk
type BusType int

const (
	// Unknown is a type of Bus
	Unknown BusType = iota
	// SCSI is a type of Bus
	SCSI
	// ATAPI is a type of Bus
	ATAPI
	// ATA is a type of Bus
	ATA
	// Firewire is a type of Bus
	Firewire
	// SSA is a type of Bus
	SSA
	// FibreChannel is a type of Bus
	FibreChannel
	// USB is a type of Bus
	USB
	// RAID is a type of Bus
	RAID
	// iSCSI is a type of Bus
	iSCSI
	// SAS is a type of Bus
	SAS
	// SATA is a type of Bus
	SATA
	// SD is a type of Bus
	SD
	// MMC is a type of Bus
	MMC
	// Virtual is a type of Bus
	Virtual
	// FileBackedVirtual is a type of Bus
	FileBackedVirtual
	// StorageSpaces is a type of Bus
	StorageSpaces
	// NVMe is a type of Bus
	NVMe
)

// BusTypeValue returns a BusType value from the human readable Bus Type name.
//
// Ref: https://docs.microsoft.com/en-us/previous-versions/windows/desktop/stormgmt/msft-disk
func BusTypeValue(b string) (BusType, error) {
	switch b {
	case "Unknown":
		return Unknown, nil
	case "SCSI":
		return SCSI, nil
	case "ATAPI":
		return ATAPI, nil
	case "ATA":
		return ATA, nil
	case "1394":
		return Firewire, nil
	case "SSA":
		return SSA, nil
	case "Fibre Channel":
		return FibreChannel, nil
	case "USB":
		return USB, nil
	case "RAID":
		return RAID, nil
	case "iSCSI":
		return iSCSI, nil
	case "SAS":
		return SAS, nil
	case "SATA":
		return SATA, nil
	case "SD":
		return SD, nil
	case "MMC":
		return MMC, nil
	case "Virtual":
		return Virtual, nil
	case "File Backed Virtual":
		return FileBackedVirtual, nil
	case "Storage Spaces":
		return StorageSpaces, nil
	case "NVMe":
		return NVMe, nil
	default:
		return Unknown, fmt.Errorf("unable to convert %s to bus type", b)
	}
}

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

	handle *ole.IDispatch
}

// Clear wipes a disk and all its contents.
//
// Example:
//		d.Clear(true, true, true)
//
// Ref: https://docs.microsoft.com/en-us/previous-versions/windows/desktop/stormgmt/clear-msft-disk
func (d *Disk) Clear(removeData, removeOEM, zeroDisk bool) (ExtendedStatus, error) {
	stat := ExtendedStatus{}
	var extendedStatus ole.VARIANT
	ole.VariantInit(&extendedStatus)
	res, err := oleutil.CallMethod(d.handle, "Clear", removeData, removeOEM, zeroDisk, &extendedStatus)
	if err != nil {
		return stat, fmt.Errorf("Clear(): %w", err)
	} else if val, ok := res.Value().(int32); val != 0 || !ok {
		return stat, fmt.Errorf("error code returned during disk wipe: %d", val)
	}
	return stat, nil
}

// Close releases the handle to the disk.
func (d *Disk) Close() {
	if d.handle != nil {
		d.handle.Release()
	}
}

// ConvertStyle converts the partition style of an already initialized disk.
//
// Ref: https://docs.microsoft.com/en-us/previous-versions/windows/desktop/stormgmt/msft-disk-convertstyle
func (d *Disk) ConvertStyle(style PartitionStyle) (ExtendedStatus, error) {
	stat := ExtendedStatus{}
	var extendedStatus ole.VARIANT
	ole.VariantInit(&extendedStatus)
	res, err := oleutil.CallMethod(d.handle, "ConvertStyle", int32(style), &extendedStatus)
	if err != nil {
		return stat, fmt.Errorf("ConvertStyle(): %w", err)
	} else if val, ok := res.Value().(int32); val != 0 || !ok {
		return stat, fmt.Errorf("error code returned during convert style: %d", val)
	}
	return stat, nil
}

// MbrType describes an MBR partition type.
type MbrType int

// MbrTypes holds the known MBR partition types.
var MbrTypes = struct {
	// FAT12 is a FAT12 file system partition.
	FAT12 MbrType
	// FAT16 is a FAT16 file system partition.
	FAT16 MbrType
	// Extended is an extended partition.
	Extended MbrType
	// Huge is a huge partition. Use this value when creating a logical volume.
	Huge MbrType
	// IFS is an NTFS or ExFAT partition.
	IFS MbrType
	// FAT32 is a FAT32 partition.
	FAT32 MbrType
}{
	FAT12:    1,
	FAT16:    4,
	Extended: 5,
	Huge:     6,
	IFS:      7,
	FAT32:    12,
}

// GptType describes a GPT partition type.
type GptType string

// GptTypes holds the known GPT partition types.
var GptTypes = struct {
	// SystemPartition is the Windows system partition.
	SystemPartition GptType
	// MicrosoftReserved is the Microsoft Reserved partition.
	MicrosoftReserved GptType
	// BasicData is a basic data partition.
	BasicData GptType
	// LDMMetadata is a Logical Disk Manager (LDM) metadata partition on a dynamic disk.
	LDMMetadata GptType
	// LDMData is an LDM data partition on a dynamic disk.
	LDMData GptType
	// MicrosoftRecovery is the Windows recovery partition.
	MicrosoftRecovery GptType
}{
	SystemPartition:   "{c12a7328-f81f-11d2-ba4b-00a0c93ec93b}",
	MicrosoftReserved: "{e3c9e316-0b5c-4db8-817d-f92df00215ae}",
	BasicData:         "{ebd0a0a2-b9e5-4433-87c0-68b6b72699c7}",
	LDMMetadata:       "{5808c8aa-7e8f-42e0-85d2-e1e90434cfb3}",
	LDMData:           "{af9b60a0-1431-4f62-bc68-3311714a69ad}",
	MicrosoftRecovery: "{de94bba4-06d1-4d40-a16a-bfd50179d6ac}",
}

// CreatePartition creates a partition on a disk.
//
// If successful, the partition is returned as a new Partition object. The new Partition must be Closed().
//
// Creating a GPT Basic Data partition, 100000000b size, drive letter "e:":
//		d.CreatePartition(100000000, false, 0, 0, "e", false, nil, &storage.GptTypes.BasicData, false, false)
//
// Creating an MBR FAT32 partition, full available space, marked active, with auto-assigned drive letter:
// 		CreatePartition(0, true, 0, 0, "", true, &storage.MbrTypes.FAT32, nil, false, true)
//
// Ref: https://docs.microsoft.com/en-us/previous-versions/windows/desktop/stormgmt/createpartition-msft-disk
func (d *Disk) CreatePartition(size uint64, useMaximumSize bool, offset uint64, alignment int, driveLetter string, assignDriveLetter bool,
	mbrType *MbrType, gptType *GptType, hidden, active bool) (Partition, ExtendedStatus, error) {
	part := Partition{}
	stat := ExtendedStatus{}

	if size > 0 && useMaximumSize {
		return part, stat, fmt.Errorf("may not specify both size and useMaximumSize")
	}
	if driveLetter != "" && assignDriveLetter {
		return part, stat, fmt.Errorf("may not specify both driveLetter and assignDriveLetter")
	}
	if mbrType != nil && gptType != nil {
		return part, stat, fmt.Errorf("cannot specify both gpt and mbr partition types")
	}

	// Several parameters have to be nil in cases where they're meant to use defaults, or where they're excluded by other options.
	var ialignment interface{}
	if alignment > 0 {
		ialignment = alignment
	} else {
		ialignment = nil
	}

	var iletter interface{}
	if driveLetter != "" {
		iletter = int16(driveLetter[0])
	} else {
		iletter = nil
	}

	var imbr interface{}
	var igpt interface{}
	if mbrType != nil {
		imbr = int(*mbrType)
		igpt = nil
	} else {
		imbr = nil
		igpt = string(*gptType)
	}

	var ioffset interface{}
	if offset > 0 {
		ioffset = strconv.FormatUint(offset, 10)
	} else {
		ioffset = nil
	}

	var isize interface{}
	if useMaximumSize {
		isize = nil
	} else {
		isize = strconv.FormatUint(size, 10)
	}

	var createdPartition ole.VARIANT
	ole.VariantInit(&createdPartition)
	var extendedStatus ole.VARIANT
	ole.VariantInit(&extendedStatus)
	res, err := oleutil.CallMethod(d.handle, "CreatePartition", isize, useMaximumSize, ioffset, ialignment, iletter, assignDriveLetter, imbr, igpt, hidden, active, &createdPartition, &extendedStatus)
	if err != nil {
		return part, stat, fmt.Errorf("CreatePartition(): %w", err)
	} else if val, ok := res.Value().(int32); val != 0 || !ok {
		return part, stat, fmt.Errorf("error code returned during partition creation: %d", val)
	}

	part.handle = createdPartition.ToIDispatch()
	return part, stat, part.Query()
}

// PartitionStyle represents the partition scheme to be used for a disk.
type PartitionStyle int32

const (
	// MbrStyle represents the MBR partition style for a disk.
	MbrStyle PartitionStyle = 1
	// GptStyle represents the GPT partition style for a disk.
	GptStyle PartitionStyle = 2
	// UnknownStyle represents an unknown partition style.
	UnknownStyle PartitionStyle = 0
)

// Initialize initializes a new disk.
//
// Example:
//		d.Initialize(storage.GptStyle)
//
// Ref: https://docs.microsoft.com/en-us/previous-versions/windows/desktop/stormgmt/initialize-msft-disk
func (d *Disk) Initialize(style PartitionStyle) (ExtendedStatus, error) {
	stat := ExtendedStatus{}
	var extendedStatus ole.VARIANT
	ole.VariantInit(&extendedStatus)
	res, err := oleutil.CallMethod(d.handle, "Initialize", int32(style), &extendedStatus)
	if err != nil {
		return stat, fmt.Errorf("Initialize(%d): %w", style, err)
	} else if val, ok := res.Value().(int32); val != 0 || !ok {
		return stat, fmt.Errorf("error code returned during initialization: %d", val)
	}
	return stat, nil
}

// Offline takes the disk offline.
//
// Example:
//		d.Offline()
//
// Ref: https://docs.microsoft.com/en-us/previous-versions/windows/desktop/stormgmt/msft-disk-offline
func (d *Disk) Offline() (ExtendedStatus, error) {
	stat := ExtendedStatus{}
	var extendedStatus ole.VARIANT
	ole.VariantInit(&extendedStatus)
	res, err := oleutil.CallMethod(d.handle, "Offline", &extendedStatus)
	if err != nil {
		return stat, fmt.Errorf("Offline(): %w", err)
	} else if val, ok := res.Value().(int32); val != 0 || !ok {
		return stat, fmt.Errorf("error code returned during offline: %d", val)
	}
	return stat, nil
}

// Online brings the disk online.
//
// Example:
//		d.Online()
//
// Ref: https://docs.microsoft.com/en-us/previous-versions/windows/desktop/stormgmt/msft-disk-online
func (d *Disk) Online() (ExtendedStatus, error) {
	stat := ExtendedStatus{}
	var extendedStatus ole.VARIANT
	ole.VariantInit(&extendedStatus)
	res, err := oleutil.CallMethod(d.handle, "Online", &extendedStatus)
	if err != nil {
		return stat, fmt.Errorf("Online(): %w", err)
	} else if val, ok := res.Value().(int32); val != 0 || !ok {
		return stat, fmt.Errorf("error code returned during online: %d", val)
	}
	return stat, nil
}

// Refresh refreshes the cached disk layout information.
//
// Example:
//		d.Refresh()
//
// Ref: https://docs.microsoft.com/en-us/previous-versions/windows/desktop/stormgmt/msft-disk-refresh
func (d *Disk) Refresh() (ExtendedStatus, error) {
	stat := ExtendedStatus{}
	var extendedStatus ole.VARIANT
	ole.VariantInit(&extendedStatus)
	res, err := oleutil.CallMethod(d.handle, "Refresh", &extendedStatus)
	if err != nil {
		return stat, fmt.Errorf("Refresh(): %w", err)
	} else if val, ok := res.Value().(int32); val != 0 || !ok {
		return stat, fmt.Errorf("error code returned during refresh: %d", val)
	}
	return stat, nil
}

// Query reads and populates the disk state.
func (d *Disk) Query() error {
	if d.handle == nil {
		return fmt.Errorf("invalid handle")
	}

	// Path
	p, err := oleutil.GetProperty(d.handle, "Path")
	if err != nil {
		return fmt.Errorf("oleutil.GetProperty(Path): %w", err)
	}
	d.Path = p.ToString()

	// Location
	p, err = oleutil.GetProperty(d.handle, "Location")
	if err != nil {
		return fmt.Errorf("oleutil.GetProperty(Location): %w", err)
	}
	d.Location = p.ToString()

	// FriendlyName
	p, err = oleutil.GetProperty(d.handle, "FriendlyName")
	if err != nil {
		return fmt.Errorf("oleutil.GetProperty(FriendlyName): %w", err)
	}
	d.FriendlyName = p.ToString()

	// UniqueID
	p, err = oleutil.GetProperty(d.handle, "UniqueId")
	if err != nil {
		return fmt.Errorf("oleutil.GetProperty(UniqueId): %w", err)
	}
	d.UniqueID = p.ToString()

	// SerialNumber
	p, err = oleutil.GetProperty(d.handle, "SerialNumber")
	if err != nil {
		return fmt.Errorf("oleutil.GetProperty(SerialNumber): %w", err)
	}
	d.SerialNumber = p.ToString()

	// FirmwareVersion
	p, err = oleutil.GetProperty(d.handle, "FirmwareVersion")
	if err != nil {
		return fmt.Errorf("oleutil.GetProperty(FirmwareVersion): %w", err)
	}
	d.FirmwareVersion = p.ToString()

	// Manufacturer
	p, err = oleutil.GetProperty(d.handle, "Manufacturer")
	if err != nil {
		return fmt.Errorf("oleutil.GetProperty(Manufacturer): %w", err)
	}
	d.Manufacturer = p.ToString()

	// Model
	p, err = oleutil.GetProperty(d.handle, "Model")
	if err != nil {
		return fmt.Errorf("oleutil.GetProperty(Model): %w", err)
	}
	d.Model = p.ToString()

	// GUID
	p, err = oleutil.GetProperty(d.handle, "Guid")
	if err != nil {
		return fmt.Errorf("oleutil.GetProperty(Guid): %w", err)
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
		prop, err := oleutil.GetProperty(d.handle, p[0].(string))
		if err != nil {
			return fmt.Errorf("oleutil.GetProperty(%s): %w", p[0].(string), err)
		}
		if err := assignVariant(prop.Value(), p[1]); err != nil {
			logger.Warningf("assignVariant(%s): %v", p[0].(string), err)
		}
	}
	return nil
}

// A DiskSet contains one or more Disks.
type DiskSet struct {
	Disks []Disk
}

// Close releases all Disk handles inside a DiskSet.
func (s *DiskSet) Close() {
	for _, d := range s.Disks {
		d.Close()
	}
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
// Close() must be called on the resulting DiskSet to ensure all disks are released.
//
// Get all disks:
//		svc.GetDisks("")
//
// To get specific disks, provide a valid WMI query filter string, for example:
//		svc.GetDisks("WHERE Number=1")
//		svc.GetDisks("WHERE IsSystem=True")
func (svc Service) GetDisks(filter string) (DiskSet, error) {
	dset := DiskSet{}
	query := "SELECT * FROM MSFT_DISK"
	if filter != "" {
		query = fmt.Sprintf("%s %s", query, filter)
	}
	raw, err := oleutil.CallMethod(svc.wmiSvc, "ExecQuery", query)
	if err != nil {
		return dset, fmt.Errorf("ExecQuery(%s): %w", query, err)
	}
	result := raw.ToIDispatch()
	defer result.Release()

	countVar, err := oleutil.GetProperty(result, "Count")
	if err != nil {
		return dset, fmt.Errorf("oleutil.GetProperty(Count): %w", err)
	}
	count := int(countVar.Val)

	for i := 0; i < count; i++ {
		d := Disk{}
		itemRaw, err := oleutil.CallMethod(result, "ItemIndex", i)
		if err != nil {
			return dset, fmt.Errorf("oleutil.CallMethod(ItemIndex, %d): %w", i, err)
		}
		d.handle = itemRaw.ToIDispatch()
		if err := d.Query(); err != nil {
			return dset, err
		}
		dset.Disks = append(dset.Disks, d)
	}

	return dset, nil
}
