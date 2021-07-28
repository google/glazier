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

// Package eventlog provides an interface to the Windows Event Log.
package eventlog

import "golang.org/x/sys/windows"

// EvtVariantData models the union inside of the EVT_VARIANT structure.
//
// Ref: https://docs.microsoft.com/en-us/windows/win32/api/winevt/ns-winevt-evt_variant
type EvtVariantData struct {
	BooleanVal    bool
	SByteVal      int8
	Int16Val      int16
	Int32Val      int32
	Int64Val      int64
	ByteVal       uint8
	UInt16Val     uint16
	UInt32Val     uint32
	UInt64Val     uint64
	SingleVal     float32
	DoubleVal     float64
	FileTimeVal   windows.Filetime
	SysTimeVal    windows.Systemtime
	GuidVal       windows.GUID
	StringVal     string
	AnsiStringVal string
	BinaryVal     byte
	SidVal        windows.SID
	SizeTVal      uint32
	BooleanArr    *[]bool
	SByteArr      *[]int8
	Int16Arr      *[]int16
	Int32Arr      *[]int32
	Int64Arr      *[]int64
	ByteArr       *[]uint16
	UInt16Arr     *[]uint16
	UInt32Arr     *[]uint32
	UInt64Arr     *[]uint64
	SingleArr     *[]float32
	DoubleArr     *[]float64
	FileTimeArr   *[]windows.Filetime
	SysTimeArr    *[]windows.Systemtime
	GuidArr       *[]windows.GUID
	StringArr     *[]string
	AnsiStringArr *[]string
	SidArr        *[]windows.SID
	SizeTArr      *[]uint32
	EvtHandleVal  windows.Handle
	XmlVal        string
	XmlValArr     *[]string
}

// EvtVariantType(EVT_VARIANT_TYPE) defines the possible data types of a EVT_VARIANT data item.
//
// Ref: https://docs.microsoft.com/en-us/windows/win32/api/winevt/ne-winevt-evt_variant_type
type EvtVariantType uint32

const (
	EvtVarTypeNull EvtVariantType = iota
	EvtVarTypeString
	EvtVarTypeAnsiString
	EvtVarTypeSByte
	EvtVarTypeByte
	EvtVarTypeInt16
	EvtVarTypeUInt16
	EvtVarTypeInt32
	EvtVarTypeUInt32
	EvtVarTypeInt64
	EvtVarTypeUInt64
	EvtVarTypeSingle
	EvtVarTypeDouble
	EvtVarTypeBoolean
	EvtVarTypeBinary
	EvtVarTypeGuid
	EvtVarTypeSizeT
	EvtVarTypeFileTime
	EvtVarTypeSysTime
	EvtVarTypeSid
	EvtVarTypeHexInt32
	EvtVarTypeHexInt64
	EvtVarTypeEvtHandle
	EvtVarTypeEvtXml
)

// EvtVariant (EVT_VARIANT) contains event data or property values.
//
// Ref: https://docs.microsoft.com/en-us/windows/win32/api/winevt/ns-winevt-evt_variant
type EvtVariant struct {
	Count uint32
	Type  EvtVariantType
	Data  EvtVariantData
}
