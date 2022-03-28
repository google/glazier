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

package helpers

import (
	"testing"

	"github.com/google/go-cmp/cmp"
)

func TestContainsString(t *testing.T) {
	tests := []struct {
		in    []string
		inStr string
		want  bool
	}{
		{
			in:    []string{"abc", "def", "ghi"},
			inStr: "def",
			want:  true,
		},
		{
			in:    []string{"abc", "def", "ghi"},
			inStr: "d",
			want:  false,
		},
		{
			in:    []string{"abc", "def", "ghi"},
			inStr: "",
			want:  false,
		},
	}
	for _, tt := range tests {
		o := ContainsString(tt.inStr, tt.in)
		if o != tt.want {
			t.Errorf("ContainsString(%s, %v) = %t, want %t", tt.inStr, tt.in, o, tt.want)
		}
	}
}

func TestStringInSlice(t *testing.T) {
	for _, tt := range []struct {
		sl  []string
		st  string
		out bool
	}{
		{[]string{"abc"}, "abc", true},
		{[]string{"abc"}, "ab", false},
		{[]string{"abc"}, "", false},
		{[]string{"abc"}, "def", false},
		{[]string{"123", "abc", "def"}, "def", true},
		{[]string{"", "abc", "def"}, "df", false},
		{[]string{}, "df", false},
		{[]string{"   "}, "df", false},
	} {
		o := StringInSlice(tt.st, tt.sl)
		if o != tt.out {
			t.Errorf("got %t, want %t", o, tt.out)
		}
	}
}

// TestStringToSlice ensures StringToSlice correctly parses passed params
func TestStringToSlice(t *testing.T) {
	tests := []struct {
		desc string
		in   string
		out  []string
	}{
		{
			desc: "comma separated",
			in:   "a,b,c",
			out:  []string{"a", "b", "c"},
		},
		{
			desc: "comma separated with spaces",
			in:   "a, b, c",
			out:  []string{"a", "b", "c"},
		},
		{
			desc: "space separated",
			in:   "a b c",
			out:  []string{"a b c"},
		},
		{
			desc: "trailing whitespace",
			in:   "a b c ",
			out:  []string{"a b c"},
		},
		{
			desc: "semicolon separated",
			in:   "a;b;c",
			out:  []string{"a;b;c"},
		},
	}
	for _, tt := range tests {
		o := StringToSlice(tt.in)
		if diff := cmp.Diff(o, tt.out); diff != "" {
			t.Errorf("TestStringToSlice(): %+v returned unexpected differences (-want +got):\n%s", tt.desc, diff)
		}
	}
}

func TestStringToMap(t *testing.T) {
	tests := []struct {
		desc string
		in   string
		out  map[string]bool
	}{
		{
			desc: "comma separated",
			in:   "a,b,c",
			out:  map[string]bool{"a": true, "b": true, "c": true},
		},
		{
			desc: "comma separated with spaces",
			in:   "a, b, c",
			out:  map[string]bool{"a": true, "b": true, "c": true},
		},
		{
			desc: "space separated",
			in:   "a b c",
			out:  map[string]bool{"a b c": true},
		},
		{
			desc: "trailing whitespace",
			in:   "a b c ",
			out:  map[string]bool{"a b c": true},
		},
		{
			desc: "semicolon separated",
			in:   "a;b;c",
			out:  map[string]bool{"a;b;c": true},
		},
		{
			desc: "empty string",
			in:   "",
			out:  map[string]bool{},
		},
	}
	for _, tt := range tests {
		o := StringToMap(tt.in)
		if diff := cmp.Diff(o, tt.out); diff != "" {
			t.Errorf("TestStringToSlice(): %+v returned unexpected differences (-want +got):\n%s", tt.desc, diff)
		}
	}
}
