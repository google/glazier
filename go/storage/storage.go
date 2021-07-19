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

// Package storage provides storage management functionality.
package storage

import (
	"encoding/json"
	"errors"
	"fmt"

	"github.com/scjalliance/comshim"
	"github.com/go-ole/go-ole"
	"github.com/go-ole/go-ole/oleutil"
	"github.com/google/winops/powershell"
)

var (
	// ErrUnmarshal indicates an error attempting to unmarshal a response from a PowerShell cmdlet.
	ErrUnmarshal = errors.New("unable to unmarshal powershell output")

	fnPSCmd = powershell.Command
)

// PartitionInfo holds information about a disk partition.
type PartitionInfo struct {
	DiskNumber      int
	IsBoot          bool
	GUID            string
	PartitionNumber int
	Size            int
	Type            string
}

// GetPartitionInfo returns information about a specific disk partition.
func GetPartitionInfo(diskNum, partNum int) (*PartitionInfo, error) {
	p := &PartitionInfo{}
	cmd := fmt.Sprintf("Get-Partition -DiskNumber %d -PartitionNumber %d | ConvertTo-JSON", diskNum, partNum)
	out, err := fnPSCmd(cmd, []string{}, nil)
	if err != nil {
		return p, err
	}
	if err = json.Unmarshal(out, p); err != nil {
		return p, fmt.Errorf("%w: %v", ErrUnmarshal, err)
	}
	return p, nil
}

// PartitionResize attempts to resize a given disk/partition.
func PartitionResize(diskNum, partNum, size int) error {
	cmd := fmt.Sprintf("Resize-Partition -DiskNumber %d -PartitionNumber %d -Size %d", diskNum, partNum, size)
	_, err := fnPSCmd(cmd, []string{}, nil)
	return err
}

// PartitionSupportedSize contains the maximum and minimum sizes supported by a partition.
type PartitionSupportedSize struct {
	SizeMin int
	SizeMax int
}

// GetPartitionSupportedSize returns the supported minimum and maximum sizes for a given disk/partition.
func GetPartitionSupportedSize(diskNum, partNum int) (*PartitionSupportedSize, error) {
	p := &PartitionSupportedSize{}
	cmd := fmt.Sprintf("Get-PartitionSupportedSize -DiskNumber %d -PartitionNumber %d | ConvertTo-JSON", diskNum, partNum)
	out, err := fnPSCmd(cmd, []string{}, nil)
	if err != nil {
		return p, err
	}
	if err = json.Unmarshal(out, p); err != nil {
		return p, fmt.Errorf("%w: %v", ErrUnmarshal, err)
	}
	return p, nil
}

// ClearDisk attempts to clean a disk by removing all partition information and un-initializing it by erasing all data on the disk
func ClearDisk(diskNum int) error {
	cmd := fmt.Sprintf("Clear-Disk -Number %d -RemoveData -RemoveOEM -Confirm:$false", diskNum)
	_, err := fnPSCmd(cmd, []string{}, nil)
	return err
}

// InitializeGPTDisk will attempt to initalize a disk
func InitializeGPTDisk(diskNum int) error {
	cmd := fmt.Sprintf("Initialize-Disk -Number %d -PartitionStyle GPT -Confirm:$false", diskNum)
	_, err := fnPSCmd(cmd, []string{}, nil)
	return err
}

// UefiPartitionInfo contains the information needed to create a UEFI Partition.
type UefiPartitionInfo struct {
	GptType     string
	DriveLetter string
	SystemLabel string
	Size        int
}

// CreateWindowsPartitions attempts to create a recovery, system, reserved and Windows partition
func CreateWindowsPartitions(diskNum int, recoveryInfo UefiPartitionInfo, SystemInfo UefiPartitionInfo, MSRInfo UefiPartitionInfo, WindowsInfo UefiPartitionInfo) error {
	var err error
	//TODO(mjo) Check if any driveLetters are currently in use and unassign / unmount them.

	err = ClearDisk(diskNum)
	if err != nil {
		return err
	}

	err = InitializeGPTDisk(diskNum)
	if err != nil {
		return err
	}

	// Create Recovery Partition.
	_, err = fnPSCmd(fmt.Sprintf("New-Partition -Disknumber %d -GptType '%s' -Size %dMB -DriveLetter '%s'", diskNum, recoveryInfo.GptType, recoveryInfo.Size, recoveryInfo.DriveLetter), []string{}, nil)
	if err != nil {
		return err
	}
	_, err = fnPSCmd(fmt.Sprintf("Format-Volume -FileSystem NTFS -NewFileSystemLabel '%s' -DriveLetter '%s'", recoveryInfo.SystemLabel, recoveryInfo.DriveLetter), []string{}, nil)
	if err != nil {
		return err
	}
	_, err = fnPSCmd(fmt.Sprintf("Set-Partition -NoDefaultDriveLetter $true -DriveLetter '%s'", recoveryInfo.DriveLetter), []string{}, nil)
	if err != nil {
		return err
	}

	// Create System Partition.
	_, err = fnPSCmd(fmt.Sprintf("New-Partition -Disknumber '%d' -GptType '%s' -Size %dMB -DriveLetter '%s'", diskNum, SystemInfo.GptType, SystemInfo.Size, SystemInfo.DriveLetter), []string{}, nil)
	if err != nil {
		return err
	}
	_, err = fnPSCmd(fmt.Sprintf("Format-Volume -FileSystem FAT32 -NewFileSystemLabel '%s' -DriveLetter '%s'", SystemInfo.SystemLabel, SystemInfo.DriveLetter), []string{}, nil)
	if err != nil {
		return err
	}

	// Create Microsoft Reserved (MSR) partition.
	_, err = fnPSCmd(fmt.Sprintf("New-Partition -GptType '%s' -Size %dMB -Disknumber '%d'", MSRInfo.GptType, MSRInfo.Size, diskNum), []string{}, nil)
	if err != nil {
		return err
	}

	// Create Windows partition by using the maximum reamaining space unless user specified.
	cmd := fmt.Sprintf("New-Partition -Disknumber %d -GptType '%s' -DriveLetter '%s' -UseMaximumSize", diskNum, WindowsInfo.GptType, WindowsInfo.DriveLetter)
	if WindowsInfo.Size != 0 {
		cmd = fmt.Sprintf("New-Partition -Disknumber %d -GptType '%s' -DriveLetter '%s' -Size %dMB", diskNum, WindowsInfo.GptType, WindowsInfo.DriveLetter, WindowsInfo.Size)
	}
	_, err = fnPSCmd(cmd, []string{}, nil)
	if err != nil {
		return err
	}
	_, err = fnPSCmd(fmt.Sprintf("Format-Volume -FileSystem NTFS -NewFileSystemLabel '%s' -DriveLetter '%s'", WindowsInfo.SystemLabel, WindowsInfo.DriveLetter), []string{}, nil)
	if err != nil {
		return err
	}

	return nil
}

// Service represents a connection to the host Storage service (in WMI).
type Service struct {
	wmiIntf *ole.IDispatch
	wmiSvc  *ole.IDispatch
}

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
	serviceRaw, err := oleutil.CallMethod(svc.wmiIntf, "ConnectServer", nil, `\\.\ROOT\Microsoft\Windows\Storage`)
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
	svc.wmiSvc.Release()
	comshim.Done()
}
