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

//go:build windows
// +build windows

// Package eventlog provides an interface to the Windows Event Log.
//
// This package is a companion package to github.com/google/winops/tree/master/winlog/wevtapi.
// The wevtapi package provides the low-level eventlog API and some of the API constants. While
// wevtapi can be used directly for event log interactions, this package aims to make common event
// log operations simpler and more organic for the typical user.
package eventlog

import (
	"bytes"
	"encoding/binary"
	"errors"
	"fmt"
	"syscall"
	"time"
	"unsafe"

	"golang.org/x/sys/windows"
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

// A Bookmark is a Handle returned by CreateBookmark
type Bookmark Handle

// Close releases a Bookmark.
func (h *Bookmark) Close() {
	if h != nil {
		wevtapi.EvtClose(h.handle)
	}
}

// Channel represents an event log channel.
type Channel struct {
	Name string
}

// ChannelConfig represents a handle to a Channel's configuration.
//
// Use Session.OpenChannelConfig to obtain a ChannelConfig.
type ChannelConfig Handle

// Close releases a ChannelConfig.
func (cc *ChannelConfig) Close() {
	if cc != nil {
		wevtapi.EvtClose(cc.handle)
	}
}

// GetProperty allows you to read a channel config's properties.
//
// PropertyID must be a wevtapi.EvtChannelConfigPropertyID.
//
// Results are returned as an EvtVariant with the corresponding property type populated.
//
// Example:
//   p, err = cc.GetProperty(wevtapi.EvtChannelConfigOwningPublisher)
// 	 if err != nil {
//	   return err
//	 }
//   fmt.Println(p.Data.StringVal)
//
// Ref: https://docs.microsoft.com/en-us/windows/win32/api/winevt/nf-winevt-evtgetchannelconfigproperty
func (cc *ChannelConfig) GetProperty(propertyID wevtapi.EvtChannelConfigPropertyID) (EvtVariant, error) {
	var bufferUsed uint32
	v := EvtVariant{}

	// Call with a null buffer to get the required buffer size.
	err := wevtapi.EvtGetChannelConfigProperty(
		cc.handle,
		propertyID,
		0,
		0,
		nil,
		&bufferUsed)
	if err != syscall.ERROR_INSUFFICIENT_BUFFER {
		return v, err
	}

	buf := make([]byte, bufferUsed)
	err = wevtapi.EvtGetChannelConfigProperty(
		cc.handle,
		propertyID,
		0,
		bufferUsed,
		unsafe.Pointer(&buf[0]),
		&bufferUsed)
	if err != nil {
		return v, err
	}

	return makeVariant(buf, 0)
}

// An Event is a Handle to an event.
type Event Handle

// Format formats a message string.
//
// MessageID is only set if using the EvtFormatMessageId flag. The ID is obtained using GetPublisherMetadataProperty.
// Set to zero if unused.
//
// Flags should be one of the EVT_FORMAT_MESSAGE_FLAGS from wevtapi.
//
// This method does not support supplying insertion values.
//
// Example (evt is an open Event from the Openssh channel):
//   pub, err := eventlog.LocalSession().OpenPublisherMetadata("Openssh", "", 2057)
//   if err != nil {
//	   return err
//	 }
// 	 defer pub.Close()
//	 out, err := evt.Format(pub, 0, wevtapi.EvtFormatMessageXml)
//	 if err != nil {
//		 return err
//	 }
//
// Ref: https://docs.microsoft.com/en-us/windows/win32/api/winevt/nf-winevt-evtformatmessage
func (e *Event) Format(pub PublisherMetadata, messageID uint32, flags uint32) (string, error) {

	// Call EvtFormatMessage with a null buffer to get the required buffer size.
	var bufferUsed uint32
	err := wevtapi.EvtFormatMessage(
		pub.handle,  // Handle to provider metadata.
		e.Handle(),  // Handle to an event.
		messageID,   // Resource identifier of the message string. Null if flag isn't EvtFormatMessageId.
		0,           // Number of values in the values parameter.
		0,           // An array of insertion values to be used when formatting the event string. Typically set to null.
		flags,       // Format message as an XML string.
		0,           // Size of buffer.
		nil,         // Null buffer.
		&bufferUsed) // Get the required buffer size.
	if !errors.Is(err, syscall.ERROR_INSUFFICIENT_BUFFER) {
		return "", err
	}

	buf := make([]uint16, bufferUsed)
	err = wevtapi.EvtFormatMessage(
		pub.handle,
		e.Handle(),
		messageID,
		0,
		0,
		flags,
		bufferUsed,
		(*byte)(unsafe.Pointer(&buf[0])),
		&bufferUsed)
	if err != nil {
		return "", err
	}

	return syscall.UTF16ToString(buf), nil
}

// Handle returns the event handle.
func (e *Event) Handle() windows.Handle {
	return e.handle
}

// Close releases an Event.
func (e *Event) Close() {
	if e != nil {
		wevtapi.EvtClose(e.handle)
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

// Handle returns the event handle.
func (rs *ResultSet) Handle() windows.Handle {
	return rs.handle
}

// Close releases a ResultSet.
func (rs *ResultSet) Close() {
	if rs != nil {
		wevtapi.EvtClose(rs.handle)
	}
}

// Next is a helper that calls eventlog.Next() for ResultSets.
func (rs *ResultSet) Next(count uint32, timeout *time.Duration) (EventSet, error) {
	return Next(rs, count, timeout)
}

// A Session is a Handle returned by OpenSession
type Session Handle

// LocalSession returns a session object that can be used for queries against the local system event log.
func LocalSession() *Session {
	return &Session{
		// API calls take a NULL session handle for local queries
	}
}

// AvailableChannels returns a slice of channels registered on the system.
//
// Ref: https://docs.microsoft.com/en-us/windows/win32/api/winevt/nf-winevt-evtopenchannelenum
// Ref: https://docs.microsoft.com/en-us/windows/win32/api/winevt/nf-winevt-evtnextchannelpath
func (s *Session) AvailableChannels() ([]Channel, error) {
	h, err := wevtapi.EvtOpenChannelEnum(s.handle, 0)
	if err != nil {
		return nil, err
	}
	defer wevtapi.EvtClose(h)

	// Enumerate all the channel names. Dynamically allocate the buffer to receive
	// channel names depending on the buffer size required as reported by the API.
	var channels []Channel
	buf := make([]uint16, 1)
	for {
		var bufferUsed uint32
		err := wevtapi.EvtNextChannelPath(h, uint32(len(buf)), &buf[0], &bufferUsed)
		switch err {
		case nil:
			channels = append(channels, Channel{Name: syscall.UTF16ToString(buf[:bufferUsed])})
		case syscall.ERROR_INSUFFICIENT_BUFFER:
			// Grow buffer.
			buf = make([]uint16, bufferUsed)
			continue
		case syscall.Errno(259): // ERROR_NO_MORE_ITEMS
			return channels, nil
		default:
			return nil, err
		}
	}
}

// AvailablePublishers returns a slice of publishers registered on the system.
func (s *Session) AvailablePublishers() ([]string, error) {
	h, err := wevtapi.EvtOpenPublisherEnum(s.handle, 0)
	if err != nil {
		return nil, fmt.Errorf("wevtapi.EvtOpenPublisherEnum failed: %v", err)
	}
	defer wevtapi.EvtClose(h)

	var publishers []string
	buf := make([]uint16, 1)
	for {
		var bufferUsed uint32
		err := wevtapi.EvtNextPublisherId(h, uint32(len(buf)), &buf[0], &bufferUsed)
		switch err {
		case nil:
			publishers = append(publishers, syscall.UTF16ToString(buf[:bufferUsed]))
		case syscall.ERROR_INSUFFICIENT_BUFFER:
			// Grow buffer.
			buf = make([]uint16, bufferUsed)
			continue
		case windows.ERROR_NO_MORE_ITEMS:
			return publishers, nil
		default:
			return nil, err
		}
	}
}

// ClearLog removes all events from the specified channel.
//
// If targetFilePath is non-empty, the contents of the channel will be exported to a file before clearing.
// If set to an empty string, the content of the channel will not be saved.
//
// Ref: https://docs.microsoft.com/en-us/windows/win32/api/winevt/nf-winevt-evtclearlog
func (s *Session) ClearLog(channelPath string, targetFilePath string) error {
	return wevtapi.EvtClearLog(
		s.handle,
		windows.StringToUTF16Ptr(channelPath),
		helpers.StringToPtrOrNil(targetFilePath),
		0, //Reserved. Must be zero.
	)
}

// Close releases a Session.
func (s *Session) Close() {
	if s != nil {
		wevtapi.EvtClose(s.handle)
	}
}

// OpenChannelConfig allows you to read and modify channel config properties.
//
// You must call Close() on the resulting ChannelConfig when finished.
//
// Example:
//   s.OpenChannelConfig("Microsoft-Windows-DriverFrameworks-UserMode/Operational")
//
// Ref: https://docs.microsoft.com/en-us/windows/win32/api/winevt/nf-winevt-evtopenchannelconfig
func (s *Session) OpenChannelConfig(logID string) (ChannelConfig, error) {
	cc := ChannelConfig{}
	var err error

	if logID == "" {
		return cc, fmt.Errorf("must supply a log id")
	}

	cc.handle, err = wevtapi.EvtOpenChannelConfig(s.handle, syscall.StringToUTF16Ptr(logID), 0)
	return cc, err
}

// OpenPublisherMetadata gets a handle that you use to read the specified provider's metadata.
//
// Publisher IDs can be enumerated by calling Session.AvailablePublishers.
//
// logFilePath is only needed if the provider is not on the local computer; otherwise leave blank.
//
// Locale can be set to an ID value from
// https://docs.microsoft.com/en-us/previous-versions/windows/embedded/ms912047(v=winembedded.10).
// Leave as zero to use the locale of the running thread.
//
// Call Close() on the PublisherMetadata once complete.
//
// Ref: https://docs.microsoft.com/en-us/windows/win32/api/winevt/nf-winevt-evtopenpublishermetadata
func (s *Session) OpenPublisherMetadata(publisherID string, logFilePath string, locale uint32) (PublisherMetadata, error) {
	var err error
	pm := PublisherMetadata{}

	ipub, err := syscall.UTF16PtrFromString(publisherID)
	if err != nil {
		return pm, err
	}

	pm.handle, err = wevtapi.EvtOpenPublisherMetadata(
		s.handle,                              // EVT_HANDLE Session
		ipub,                                  // LPCWSTR    PublisherId
		helpers.StringToPtrOrNil(logFilePath), //	LPCWSTR LogFilePath
		locale,                                // LCID       Locale
		0,                                     // Reserved. Must be zero.
	)

	// If there is no publisher metadata available return the original event.
	if err == syscall.ERROR_FILE_NOT_FOUND {
		return pm, fmt.Errorf("no publisher metadata")
	} else if err != nil {
		return pm, err
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
// 	 conn, err := eventlog.LocalSession().Query("Windows Powershell", "*", wevtapi.EvtQueryReverseDirection)
// 	 if err != nil {
//     return err
//	 }
//	 defer conn.Close()
//
// Ref: https://docs.microsoft.com/en-us/windows/win32/api/winevt/nf-winevt-evtquery
func (s *Session) Query(path string, query string, flags uint32) (ResultSet, error) {
	var rs ResultSet
	var err error

	rs.handle, err = wevtapi.EvtQuery(s.handle, windows.StringToUTF16Ptr(path), windows.StringToUTF16Ptr(query), flags)
	if err != nil {
		return rs, err
	}
	if rs.handle == windows.InvalidHandle {
		return rs, errors.New("invalid query")
	}
	return rs, nil
}

// Subscribe creates a subscription that will receive current and/or future events from a channel or log file
// which match the specified query criteria.
//
// This method uses SignalEvent rather than Callback for notifying of new events. You may create and provide a custom signal event using
// windows.CreateEvent. If signalEvent is left as nil, a default event will be created for you. In either case, the event is returned inside the
// resulting Subscription. This subscription model is referred to as a "pull subscription", as you must watch for the signal events to
// arrive, and use Next to obtain the results.
//
// channelPath and query can be used in multiple combinations, including xpath and structured xml. See the API documentation for details.
//
// Bookmark should be supplied if using the EvtSubscribeStartAfterBookmark flag. Otherwise it should be left as nil.
//
// Flags should be one or more of the EVT_SUBSCRIBE_FLAGS from wevtapi.
//
// You must call Close() on the resulting Subscription when finished.
//
// Ref: https://docs.microsoft.com/en-us/windows/win32/api/winevt/nf-winevt-evtsubscribe
func (s *Session) Subscribe(signalEvent *windows.Handle, channelPath string, query string, bookmark *Bookmark, flags uint32) (Subscription, error) {
	sub := Subscription{}
	var err error

	if signalEvent != nil {
		sub.SignalEvent = *signalEvent
	} else {
		sub.SignalEvent, err = windows.CreateEvent(
			nil, // Default security descriptor.
			1,   // Manual reset.
			1,   // Initial state is signaled.
			nil) // Optional name.
		if err != nil {
			return sub, err
		}
	}

	if bookmark == nil {
		bookmark = &Bookmark{} // bookmark is nil unless using EvtSubscribeStartAfterBookmark
	}

	sub.handle, err = wevtapi.EvtSubscribe(
		s.handle,
		sub.SignalEvent,
		helpers.StringToPtrOrNil(channelPath),
		helpers.StringToPtrOrNil(query),
		bookmark.handle,
		uintptr(0),
		uintptr(0), // nil for signal-based subscription
		uint32(flags))

	return sub, err
}

// Subscription tracks an event subscription created by Session.Subscribe.
type Subscription struct {
	handle      windows.Handle
	SignalEvent windows.Handle
}

// Close releases a Subscription.
func (s *Subscription) Close() {
	if s != nil {
		wevtapi.EvtClose(s.handle)
		wevtapi.EvtClose(s.SignalEvent)
	}
}

// Handle returns the subscription handle.
func (s *Subscription) Handle() windows.Handle {
	return s.handle
}

// Next attempts to get the next available events for the subscription.
func (s *Subscription) Next(count uint32, timeout *time.Duration) (EventSet, error) {
	return Next(s, count, timeout)
}

// WaitForSignal waits for new events to arrive via the SignalEvent. Returns true if the event
// was signalled before the timeout expired. Timeout must be between 0 and 2^32us.
func (s *Subscription) WaitForSignal(timeout time.Duration) (bool, error) {
	status, err := windows.WaitForSingleObject(s.SignalEvent, uint32(timeout/time.Millisecond))
	if err != nil {
		return false, err
	}
	return status == syscall.WAIT_OBJECT_0, nil
}

// CreateBookmark creates a bookmark that identifies an event in a channel.
func CreateBookmark(bookmark string) (Bookmark, error) {
	book := Bookmark{}
	var err error
	book.handle, err = wevtapi.EvtCreateBookmark(helpers.StringToPtrOrNil(bookmark))
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

// An EventGenerator provides a handle to a query or subscription that may yield events.
type EventGenerator interface {
	Handle() windows.Handle
}

// Next gets the next event(s) returned by a query or subscription.
//
// Ref: https://docs.microsoft.com/en-us/windows/win32/api/winevt/nf-winevt-evtnext
func Next(handle EventGenerator, count uint32, timeout *time.Duration) (EventSet, error) {
	es := EventSet{}

	defaultTimeout := 2000 * time.Millisecond
	if timeout == nil {
		timeout = &defaultTimeout
	}

	// Get handles to events from the result set.
	evts := make([]windows.Handle, count)
	err := wevtapi.EvtNext(
		handle.Handle(),                // Handle to query or subscription result set.
		count,                          // The number of events to attempt to retrieve.
		&evts[0],                       // Pointer to the array of event handles.
		uint32(timeout.Milliseconds()), // Timeout in milliseconds to wait.
		0,                              // Reserved. Must be zero.
		&es.Count)                      // The number of handles in the array that are set by the API.
	if errors.Is(err, windows.ERROR_NO_MORE_ITEMS) {
		return es, err
	} else if err != nil {
		return es, fmt.Errorf("wevtapi.EvtNext: %w", err)
	}

	for i := 0; i < int(es.Count); i++ {
		es.Events = append(es.Events, Event{handle: evts[i]})
	}

	return es, nil
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

// EvtVariantType (EVT_VARIANT_TYPE) defines the possible data types of a EVT_VARIANT data item.
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

// RawVariant is like EvtVariant but holds the raw, un-typed data in the Data field.
type RawVariant struct {
	Data  uint64
	Count uint32
	Type  uint32
}

// EvtVariant (EVT_VARIANT) contains event data or property values.
//
// Ref: https://docs.microsoft.com/en-us/windows/win32/api/winevt/ns-winevt-evt_variant
type EvtVariant struct {
	Count uint32
	Type  EvtVariantType
	Data  EvtVariantData
}

// MakeVariant attempts to make an EvtVariant from a raw buffer.
func makeVariant(buf []byte, index int) (EvtVariant, error) {
	ev := EvtVariant{}
	raw := RawVariant{}

	// In evt_variant arrays, each variant is offset by 16; the index gives us the location
	// we're supposed to look at.
	start := index * 16
	end := start + 16

	// Put the buffer slice into a RawVariant so we can type it
	if err := binary.Read(
		bytes.NewBuffer(buf[start:end]), binary.LittleEndian, &raw); err != nil {
		return ev, err
	}

	// The EVT_VARIANT union can be holding any of the union's supported data types.
	// To make it useable, we look for the type in the Type field and cast accordingly.
	ev.Type = EvtVariantType(raw.Type)
	switch raw.Type {
	case uint32(EvtVarTypeNull):
		return ev, nil
	case uint32(EvtVarTypeString):
		ptr := *(**uint16)(unsafe.Pointer(&raw.Data))
		ev.Data.StringVal = windows.UTF16PtrToString(ptr)
	case uint32(EvtVarTypeSByte):
		ev.Data.SByteVal = *(*int8)(unsafe.Pointer(&raw.Data))
	case uint32(EvtVarTypeByte):
		ev.Data.ByteVal = *(*uint8)(unsafe.Pointer(&raw.Data))
	case uint32(EvtVarTypeInt16):
		ev.Data.Int16Val = *(*int16)(unsafe.Pointer(&raw.Data))
	case uint32(EvtVarTypeInt32), uint32(EvtVarTypeHexInt32):
		ev.Data.Int32Val = *(*int32)(unsafe.Pointer(&raw.Data))
	case uint32(EvtVarTypeInt64), uint32(EvtVarTypeHexInt64):
		ev.Data.Int64Val = *(*int64)(unsafe.Pointer(&raw.Data))
	case uint32(EvtVarTypeUInt16):
		ev.Data.UInt16Val = *(*uint16)(unsafe.Pointer(&raw.Data))
	case uint32(EvtVarTypeUInt32):
		ev.Data.UInt32Val = *(*uint32)(unsafe.Pointer(&raw.Data))
	case uint32(EvtVarTypeUInt64):
		ev.Data.UInt64Val = *(*uint64)(unsafe.Pointer(&raw.Data))
	case uint32(EvtVarTypeBoolean):
		ev.Data.BooleanVal = *(*bool)(unsafe.Pointer(&raw.Data))
	case uint32(EvtVarTypeGuid):
		ev.Data.GuidVal = *(*windows.GUID)(unsafe.Pointer(&raw.Data))
	case uint32(EvtVarTypeFileTime):
		ev.Data.FileTimeVal = *(*windows.Filetime)(unsafe.Pointer(&raw.Data))
	case uint32(EvtVarTypeSid):
		ev.Data.SidVal = *(*windows.SID)(unsafe.Pointer(&raw.Data))
	case uint32(EvtVarTypeSysTime):
		ev.Data.SysTimeVal = *(*windows.Systemtime)(unsafe.Pointer(&raw.Data))
	default:
		return ev, fmt.Errorf("unsupported type %v", raw.Type)
	}
	return ev, nil
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
	if !errors.Is(err, syscall.ERROR_INSUFFICIENT_BUFFER) {
		return "", err
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
		return "", err
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
	if !errors.Is(err, syscall.ERROR_INSUFFICIENT_BUFFER) {
		return nil, err
	}

	// Create a buffer to hold the EVT_VARIANT objects returned by the query.
	//
	// Ref: https://docs.microsoft.com/en-us/windows/win32/api/winevt/ns-winevt-evt_variant

	buf := make([]byte, bufferUsed)
	// Render the fragment according to the flag.
	if err = wevtapi.EvtRender(
		renderCtx.handle,
		fragment.Handle(),
		wevtapi.EvtRenderEventValues,
		bufferUsed,
		unsafe.Pointer(&buf[0]),
		&bufferUsed,
		&propertyCount); err != nil {
		return nil, err
	}

	for i := 0; i < int(propertyCount); i++ {
		v, err := makeVariant(buf, i)
		if err != nil {
			return vals, err
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
