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

package device

import (
	"io/ioutil"
	"os"
	"path/filepath"
	"testing"

	"github.com/google/go-cmp/cmp"
)

func TestUserProfiles(t *testing.T) {
	root, err := ioutil.TempDir(os.TempDir(), "")
	if err != nil {
		t.Fatalf("ioutil.TempDir: %v", err)
	}
	users := []string{"Administrator", "George", "Public"}
	for _, u := range users {
		if err := os.MkdirAll(filepath.Join(root, "/Users/", u), 644); err != nil {
			t.Fatalf("os.MkdirAll: %v", err)
		}
	}
	if err := os.Setenv("SystemDrive", root); err != nil {
		t.Fatalf("os.Setenv: %v", err)
	}
	out, err := UserProfiles()
	if err != nil {
		t.Errorf("UserProfiles() returned unexpected error %v", err)
	}
	if diff := cmp.Diff(out, users); diff != "" {
		t.Errorf("UserProfiles() returned unexpected diff (-want +got):\n%s", diff)
	}
}
