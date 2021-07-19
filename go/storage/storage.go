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

// ExtendedStatus is a placeholder for MSFT_StorageExtendedStatus
//
// Ref: https://docs.microsoft.com/en-us/previous-versions/windows/desktop/stormgmt/msft-storageextendedstatus
type ExtendedStatus struct {}

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
