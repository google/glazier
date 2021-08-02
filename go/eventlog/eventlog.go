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

// +build windows

// Package eventlog provides an interface to the Windows Event Log.
package eventlog

import (
	"errors"
	"fmt"
	"syscall"
	"time"
	"unsafe"

	"golang.org/x/sys/windows"
	"github.com/google/logger"
	"github.com/google/glazier/go/helpers"
	"github.com/google/winops/winlog/wevtapi"
)

// Handle maps a handle to an event log resource (EVT_HANDLE). Close() must be called to release the handle.
//
// Note that the order in which handles are closed may matter. Parent handles should not be closed until all
// uses of the handles (queries, etc) are complete.
//
// Ref: https://docs.microsoft.com/en-us/windows/win32/api/winevt/nf-winevt-evtclose
type Handle struct {
	handle windows.Handle
}

// Close releases a Handle.
func (h *Handle) Close() {
	if h != nil {
		wevtapi.EvtClose(h.handle)
	}
}

// A Bookmark is a Handle returned by CreateBookmark
type Bookmark Handle

// Close releases a Bookmark.
func (h *Bookmark) Close() {
	if h != nil {
		wevtapi.EvtClose(h.handle)
	}
}

// An Event is a Handle to an event.
type Event Handle

// Close releases an Event.
func (h *Event) Close() {
	if h != nil {
		wevtapi.EvtClose(h.handle)
	}
}

// PublisherMetadata is a Handle which tracks provider metadata.
type PublisherMetadata Handle

// Close releases a RenderContext.
func (h *PublisherMetadata) Close() {
	if h != nil {
		wevtapi.EvtClose(h.handle)
	}
}

// A RenderContext is a Handle which tracks a Context as returned by EvtCreateRenderContext.
type RenderContext Handle

// Close releases a RenderContext.
func (h *RenderContext) Close() {
	if h != nil {
		wevtapi.EvtClose(h.handle)
	}
}

// A ResultSet is a Handle returned by a Query or Subscription
type ResultSet Handle

// Close releases a ResultSet.
func (h *ResultSet) Close() {
	if h != nil {
		wevtapi.EvtClose(h.handle)
	}
}

// A Session is a Handle returned by OpenSession
type Session Handle

// Close releases a Session.
func (h *Session) Close() {
	if h != nil {
		wevtapi.EvtClose(h.handle)
	}
}

// CreateBookmark creates a bookmark that identifies an event in a channel.
func CreateBookmark(bookmark string) (Bookmark, error) {
	book := Bookmark{}
	var err error
	if bookmark != "" {
		book.handle, err = wevtapi.EvtCreateBookmark(windows.StringToUTF16Ptr(bookmark))
	} else {
		book.handle, err = wevtapi.EvtCreateBookmark(nil)
	}
	return book, err
}

// EvtRenderContextFlags specify which types of values to render from a given event.
//
// Ref: https://docs.microsoft.com/en-us/windows/win32/api/winevt/ne-winevt-evt_render_context_flags
type EvtRenderContextFlags uint32

const (
	// EvtRenderContextValues renders specific properties from the event.
	EvtRenderContextValues EvtRenderContextFlags = iota
	// EvtRenderContextSystem renders the system properties under the System element.
	EvtRenderContextSystem
	// EvtRenderContextUser renders all user-defined properties under the UserData or EventData element.
	EvtRenderContextUser
)

// CreateRenderContext creates a context that specifies the information in the event that you want to render.
//
// The RenderContext is used to obtain only a subset of event data when querying events.
// Without a RenderContext, the entirety of the log data will be returned.
//
// Passing one of EvtRenderContextSystem or EvtRenderContextUser (with valuePaths nil)
// will render all properties under the corresponding element (System or User). Passing
// EvtRenderContextValues along with a list of valuePaths allows the caller to obtain individual
// event elements. valuePaths must be well formed XPath expressions. See the documentation
// for EvtCreateRenderContext and EVT_RENDER_CONTEXT_FLAGS for more detail.
//
// Example, rendering all System values:
//		eventlog.CreateRenderContext(eventlog.EvtRenderContextSystem, nil)
//
// Example, rendering specific values:
//		eventlog.CreateRenderContext(eventlog.EvtRenderContextValues, &[]string{
//				"Event/System/TimeCreated/@SystemTime", "Event/System/Provider/@Name"})
//
// Ref: https://docs.microsoft.com/en-us/windows/win32/api/winevt/nf-winevt-evtcreaterendercontext
func CreateRenderContext(flags EvtRenderContextFlags, valuePaths *[]string) (RenderContext, error) {
	rc := RenderContext{}

	pathsPtr := uintptr(0)
	p := []*uint16{}
	if valuePaths != nil {
		for _, v := range *valuePaths {
			ptr, err := syscall.UTF16PtrFromString(v)
			if err != nil {
				return rc, fmt.Errorf("syscall.UTF16PtrFromString(%s): %w", v, err)
			}
			p = append(p, ptr)
		}
		pathsPtr = uintptr(unsafe.Pointer(&p[0]))
	}

	var err error
	rc.handle, err = wevtapi.EvtCreateRenderContext(uint32(len(p)), uintptr(pathsPtr), uint32(flags))
	return rc, err
}

// An EventSet holds one or more event handles.
//
// Close() must be called to release the event handles when finished.
type EventSet struct {
	Events []Event
	Count  uint32
}

// Close releases all events in the EventSet.
func (e *EventSet) Close() {
	for _, evt := range e.Events {
		evt.Close()
	}
}

// Next gets the next event(s) returned by a query or subscription.
//
// Ref: https://docs.microsoft.com/en-us/windows/win32/api/winevt/nf-winevt-evtnext
func Next(handle ResultSet, count uint32, timeout *time.Duration) (EventSet, error) {
	es := EventSet{}

	defaultTimeout := 2000 * time.Millisecond
	if timeout == nil {
		timeout = &defaultTimeout
	}

	// Get handles to events from the result set.
	evts := make([]windows.Handle, count)
	err := wevtapi.EvtNext(
		handle.handle,                  // Handle to query or subscription result set.
		count,                          // The number of events to attempt to retrieve.
		&evts[0],                       // Pointer to the array of event handles.
		uint32(timeout.Milliseconds()), // Timeout in milliseconds to wait.
		0,                              // Reserved. Must be zero.
		&es.Count)                      // The number of handles in the array that are set by the API.
	if err == windows.ERROR_NO_MORE_ITEMS {
		return es, err
	} else if err != nil {
		return es, fmt.Errorf("wevtapi.EvtNext: %w", err)
	}

	for i := 0; i < int(es.Count); i++ {
		es.Events = append(es.Events, Event{handle: evts[i]})
	}

	return es, nil
}

// OpenPublisherMetadata gets a handle that you use to read the specified provider's metadata.
//
// Call Close() on the PublisherMetadata once complete.
//
// Ref: https://docs.microsoft.com/en-us/windows/win32/api/winevt/nf-winevt-evtopenpublishermetadata
func OpenPublisherMetadata(session *Session, publisherID string, logFilePath string, locale uint32) (PublisherMetadata, error) {
	var err error
	pm := PublisherMetadata{}

	var s windows.Handle
	if session != nil {
		s = session.handle
	}

	ipub, err := syscall.UTF16PtrFromString(publisherID)
	if err != nil {
		return pm, fmt.Errorf("syscall.UTF16PtrFromString failed: %v", err)
	}

	pm.handle, err = wevtapi.EvtOpenPublisherMetadata(
		s,                                     // EVT_HANDLE Session
		ipub,                                  // LPCWSTR    PublisherId
		helpers.StringToPtrOrNil(logFilePath), //	LPCWSTR LogFilePath
		locale,                                // LCID       Locale
		0,                                     // Reserved. Must be zero.
	)

	// If there is no publisher metadata available return the original event.
	if err == syscall.ERROR_FILE_NOT_FOUND {
		return pm, fmt.Errorf("no publisher metadata")
	} else if err != nil {
		return pm, fmt.Errorf("OpenPublisherMetadata failed: %v", err)
	}

	return pm, nil
}

// Query runs a query to retrieve events from a channel or log file that match the specified query criteria.
//
// Session is only required for remote connections; leave as nil for the local log. Flags can be any of
// wevtapi.EVT_QUERY_FLAGS.
//
// The session handle must remain open until all subsequent processing on the query results have completed. Call
// Close() once complete.
//
// Example:
// 	 conn, err := eventlog.Query(nil, "Windows Powershell", "*", wevtapi.EvtQueryReverseDirection)
// 	 if err != nil {
//     return err
//	 }
//	 defer conn.Close()
//
// Ref: https://docs.microsoft.com/en-us/windows/win32/api/winevt/nf-winevt-evtquery
func Query(session *Session, path string, query string, flags uint32) (ResultSet, error) {
	var rs ResultSet
	var err error

	var s windows.Handle
	if session != nil {
		s = session.handle
	}
	rs.handle, err = wevtapi.EvtQuery(s, windows.StringToUTF16Ptr(path), windows.StringToUTF16Ptr(query), flags)
	if err != nil {
		return rs, fmt.Errorf("EvtQuery: %w", err)
	}
	if rs.handle == windows.InvalidHandle {
		return rs, errors.New("invalid query")
	}
	return rs, nil
}

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

// Fragment describes a renderable fragment; an event or to a bookmark.
type Fragment interface {
	Handle() windows.Handle
}

// Render renders a fragment (bookmark or event) as an XML string.
//
// This function renders the entire fragment as XML. To render only specific elements of the event, use RenderValues.
//
// Flags can be either EvtRenderEventValues or EvtRenderEventXml.
//
// Ref: https://docs.microsoft.com/en-us/windows/win32/api/winevt/nf-winevt-evtrender
func Render(fragment Fragment, flag uint32) (string, error) {
	var bufferUsed uint32
	var propertyCount uint32

	if flag == wevtapi.EvtRenderEventValues {
		return "", fmt.Errorf("EvtRenderEventValues requires the RenderValues function")
	}

	// Call EvtRender with a null buffer to get the required buffer size.
	err := wevtapi.EvtRender(
		0,
		fragment.Handle(),
		flag,
		0,
		nil,
		&bufferUsed,
		&propertyCount)
	if err != syscall.ERROR_INSUFFICIENT_BUFFER {
		return "", fmt.Errorf("wevtapi.EvtRender: %w", err)
	}

	// Create a buffer based on the buffer size required.
	buf := make([]uint16, bufferUsed/2)

	// Render the fragment according to the flag.
	if err = wevtapi.EvtRender(
		0,
		fragment.Handle(),
		flag,
		bufferUsed,
		unsafe.Pointer(&buf[0]),
		&bufferUsed,
		&propertyCount); err != nil {
		return "", fmt.Errorf("wevtapi.EvtRender: %w", err)
	}

	return syscall.UTF16ToString(buf), nil
}

// RenderValues renders specific elements from a fragment (event).
//
// You must supply a RenderContext from CreateRenderContext. The RenderContext determines which values are rendered from the fragment.
//
// The rendered events are returned by Windows as variants (EVT_VARIANT) in a wide variety of types. We do our best to
// cast these into Go types, and return the results encapsulated in an EvtVariantData. EvtVariantData holds all possible types, but
// only the rendered value should be non-nil on return. The EvtVariant.Type field will indicate which of the EvtVariantData fields
// should hold the rendered data.
//
// For example, rendering a string fragment successfully should return:
//		EvtVariant {
//			Type: EvtVarTypeString
//			Data: EvtVariantData {
//				...
//				StringVal: "my rendered string"
//				...
//			}
//		}
//
// Ref: https://docs.microsoft.com/en-us/windows/win32/api/winevt/nf-winevt-evtrender
// Ref: https://docs.microsoft.com/en-us/windows/win32/api/winevt/ns-winevt-evt_variant
func RenderValues(renderCtx RenderContext, fragment Fragment) ([]EvtVariant, error) {
	var bufferUsed uint32
	var propertyCount uint32
	var vals []EvtVariant

	// Call EvtRender with a null buffer to get the required buffer size.
	err := wevtapi.EvtRender(
		renderCtx.handle,
		fragment.Handle(),
		wevtapi.EvtRenderEventValues,
		0,
		nil,
		&bufferUsed,
		&propertyCount)
	if err != syscall.ERROR_INSUFFICIENT_BUFFER {
		return nil, fmt.Errorf("wevtapi.EvtRender: %w", err)
	}

	// Create a buffer to hold the EVT_VARIANT objects returned by the query.
	//
	// Ref: https://docs.microsoft.com/en-us/windows/win32/api/winevt/ns-winevt-evt_variant
	buf := make([]struct {
		Raw   [8]byte // Go represents the union as a byte slice, sized based on the largest element in the union.
		Count uint32
		Type  uint32
	}, propertyCount)

	// Render the fragment according to the flag.
	if err = wevtapi.EvtRender(
		renderCtx.handle,
		fragment.Handle(),
		wevtapi.EvtRenderEventValues,
		bufferUsed,
		unsafe.Pointer(&buf[0]),
		&bufferUsed,
		&propertyCount); err != nil {
		return nil, fmt.Errorf("wevtapi.EvtRender: %w", err)
	}

	// The EVT_VARIANT union can be holding any of the union's supported data types.
	// To make it useable, we look for the type in the Type field and cast accordingly.
	for i := 0; i < int(propertyCount); i++ {
		v := EvtVariant{Type: EvtVariantType(buf[i].Type)}
		switch buf[i].Type {
		case uint32(EvtVarTypeNull):
			continue
		case uint32(EvtVarTypeString):
			ptr := *(**uint16)(unsafe.Pointer(&buf[i].Raw))
			v.Data.StringVal = windows.UTF16PtrToString(ptr)
		case uint32(EvtVarTypeSByte):
			v.Data.SByteVal = *(*int8)(unsafe.Pointer(&buf[i].Raw))
		case uint32(EvtVarTypeByte):
			v.Data.ByteVal = *(*uint8)(unsafe.Pointer(&buf[i].Raw))
		case uint32(EvtVarTypeInt16):
			v.Data.Int16Val = *(*int16)(unsafe.Pointer(&buf[i].Raw))
		case uint32(EvtVarTypeInt32), uint32(EvtVarTypeHexInt32):
			v.Data.Int32Val = *(*int32)(unsafe.Pointer(&buf[i].Raw))
		case uint32(EvtVarTypeInt64), uint32(EvtVarTypeHexInt64):
			v.Data.Int64Val = *(*int64)(unsafe.Pointer(&buf[i].Raw))
		case uint32(EvtVarTypeUInt16):
			v.Data.UInt16Val = *(*uint16)(unsafe.Pointer(&buf[i].Raw))
		case uint32(EvtVarTypeUInt32):
			v.Data.UInt32Val = *(*uint32)(unsafe.Pointer(&buf[i].Raw))
		case uint32(EvtVarTypeUInt64):
			v.Data.UInt64Val = *(*uint64)(unsafe.Pointer(&buf[i].Raw))
		case uint32(EvtVarTypeBoolean):
			v.Data.BooleanVal = *(*bool)(unsafe.Pointer(&buf[i].Raw))
		case uint32(EvtVarTypeGuid):
			v.Data.GuidVal = *(*windows.GUID)(unsafe.Pointer(&buf[i].Raw))
		case uint32(EvtVarTypeFileTime):
			v.Data.FileTimeVal = *(*windows.Filetime)(unsafe.Pointer(&buf[i].Raw))
		case uint32(EvtVarTypeSid):
			v.Data.SidVal = *(*windows.SID)(unsafe.Pointer(&buf[i].Raw))
		case uint32(EvtVarTypeSysTime):
			v.Data.SysTimeVal = *(*windows.Systemtime)(unsafe.Pointer(&buf[i].Raw))
		default:
			logger.Warningf("Unsupported type: %v", buf[i].Type)
		}
		vals = append(vals, v)
	}

	return vals, nil
}

// UpdateBookmark updates a bookmark with information that identifies the specified event.
//
// Ref: https://docs.microsoft.com/en-us/windows/win32/api/winevt/nf-winevt-evtupdatebookmark
func UpdateBookmark(bookmark Bookmark, event Event) error {
	return wevtapi.EvtUpdateBookmark(bookmark.handle, event.handle)
}
