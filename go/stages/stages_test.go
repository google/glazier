// Copyright 2020 Google LLC
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
package stages

import (
	"fmt"
	"testing"
	"time"

	"github.com/google/go-cmp/cmp"
	"github.com/pkg/errors"
	"golang.org/x/sys/windows/registry"
)

const (
	testStageRoot = `SOFTWARE\Glazier\Testing`
	testTime      = "2019-11-06T17:37:43.279253"
)

func createTestKeys(subKeys ...string) error {
	k, _, err := registry.CreateKey(registry.LOCAL_MACHINE, testStageRoot, registry.CREATE_SUB_KEY)
	if err != nil {
		return err
	}
	defer k.Close()
	for _, id := range subKeys {
		sk, _, err := registry.CreateKey(k, id, registry.CREATE_SUB_KEY)
		if err != nil {
			return err
		}
		defer sk.Close()
		k = sk
	}
	return nil
}

func cleanupTestKey() error {
	return registry.DeleteKey(registry.LOCAL_MACHINE, testStageRoot)
}

func TestActiveStageNoRootKey(t *testing.T) {
	testID := "TestActiveStageNoRootKey"
	stage, err := activeStageFromReg(testStageRoot + `\` + testID)
	if err != nil {
		t.Errorf("%s(): raised unexpected error %v", testID, err)
	}
	if stage != "0" {
		t.Errorf("%s(): got %s, want %s", testID, stage, "0")
	}
}

func TestActiveStageNoActiveKey(t *testing.T) {
	testID := "TestActiveStageNoActiveKey"
	if err := createTestKeys(testID); err != nil {
		t.Fatal(err)
	}
	defer cleanupTestKey()

	stage, err := activeStageFromReg(testStageRoot + `\` + testID)
	if err != nil {
		t.Errorf("%s(): raised unexpected error %v", testID, err)
	}
	if stage != "0" {
		t.Errorf("%s(): got %s, want %s", testID, stage, "0")
	}
}

func TestActiveStageInProgress(t *testing.T) {
	testID := "TestActiveStageInProgress"
	subKey := testStageRoot + `\` + testID

	if err := createTestKeys(testID); err != nil {
		t.Fatal(err)
	}
	defer cleanupTestKey()

	k, err := registry.OpenKey(registry.LOCAL_MACHINE, subKey, registry.WRITE)
	if err != nil {
		t.Fatal(err)
	}
	if err = k.SetStringValue("_Active", "2"); err != nil {
		t.Fatal(err)
	}
	k.Close()

	stage, err := activeStageFromReg(subKey)
	if err != nil {
		t.Errorf("%s(): raised unexpected error %v", testID, err)
	}
	if stage != "2" {
		t.Errorf("%s(): got %s, want %s", testID, stage, "2")
	}
}

func TestActiveStageTypeError(t *testing.T) {
	testID := "TestActiveStageTypeHandling"
	subKey := testStageRoot + `\` + testID

	if err := createTestKeys(testID); err != nil {
		t.Fatal(err)
	}
	defer cleanupTestKey()

	k, err := registry.OpenKey(registry.LOCAL_MACHINE, subKey, registry.WRITE)
	if err != nil {
		t.Fatal(err)
	}
	if err = k.SetDWordValue("_Active", 0); err != nil {
		t.Fatal(err)
	}
	k.Close()

	if _, err := activeStageFromReg(subKey); err == nil {
		t.Errorf("%s(): failed to raise expected error", testID)
	}
}

func TestRetreiveTimes(t *testing.T) {
	testID := "TestRetreiveTimes"
	testKey := fmt.Sprintf(`%s\%s`, testStageRoot, testID)
	stageKey := fmt.Sprintf(`%s\%d`, testKey, 5)

	if err := createTestKeys(testID, "5"); err != nil {
		t.Fatal(err)
	}
	defer cleanupTestKey()

	k, err := registry.OpenKey(registry.LOCAL_MACHINE, stageKey, registry.WRITE)
	if err != nil {
		t.Fatal(err)
	}
	if err = k.SetStringValue("Start", testTime); err != nil {
		t.Fatal(err)
	}
	k.Close()
	s := NewStage()
	err = s.RetreiveTimes(testKey, "5")
	if err != nil {
		t.Errorf("%s(): raised unexpected error %v", testID, err)
	}

	at, _ := time.Parse(timeFmt, testTime)
	if diff := cmp.Diff(at, s.Start); diff != "" {
		t.Errorf("%s(): returned unexpected diff (-want +got):\n%s", testID, diff)
	}
}

func TestRetreiveTimesParseError(t *testing.T) {
	testID := "TestRetreiveTimesParseError"
	testKey := fmt.Sprintf(`%s\%s`, testStageRoot, testID)
	stageKey := fmt.Sprintf(`%s\%d`, testKey, 5)

	if err := createTestKeys(testID, "5"); err != nil {
		t.Fatal(err)
	}
	defer cleanupTestKey()

	k, err := registry.OpenKey(registry.LOCAL_MACHINE, stageKey, registry.WRITE)
	if err != nil {
		t.Fatal(err)
	}
	if err = k.SetStringValue("Start", "20191106V17:37:43"); err != nil {
		t.Fatal(err)
	}
	k.Close()
	s := NewStage()
	err = s.RetreiveTimes(testKey, "5")
	if err == nil {
		t.Errorf("%s(): failed to raise expected error", testID)
	}
}

func TestActiveTimeFromReg(t *testing.T) {
	at, _ := time.Parse(timeFmt, testTime)
	tests := []struct {
		desc    string
		in      string
		period  string
		want    time.Time
		wantErr error
	}{
		{
			desc:    "key exists",
			in:      "3",
			period:  "Start",
			want:    at,
			wantErr: nil,
		},
		{
			desc:    "key does not exist",
			in:      "6",
			period:  "End",
			want:    time.Time{},
			wantErr: nil,
		},
		{
			desc:    "wrong period",
			in:      "3",
			period:  "Foo",
			want:    time.Time{},
			wantErr: ErrPeriod,
		},
	}

	testID := "TestActiveTimeFromReg"
	testKey := fmt.Sprintf(`%s\%s`, testStageRoot, testID)
	stageKey := fmt.Sprintf(`%s\%d`, testKey, 3)

	if err := createTestKeys(testID, "3"); err != nil {
		t.Fatal(err)
	}
	defer cleanupTestKey()

	k, err := registry.OpenKey(registry.LOCAL_MACHINE, stageKey, registry.WRITE)
	if err != nil {
		t.Fatal(err)
	}
	if err = k.SetStringValue("Start", testTime); err != nil {
		t.Fatal(err)
	}
	k.Close()

	for _, tt := range tests {
		got, err := activeTimeFromReg(testKey, tt.in, tt.period)
		if !errors.Is(err, tt.wantErr) {
			t.Errorf("activeTimeFromReg(%v, %v, %v) returned unexpected error %v", testStageRoot, tt.in, tt.period, err)
		}
		if diff := cmp.Diff(tt.want, got); diff != "" {
			t.Errorf("activeTimeFromReg(%v, %v, %v) returned unexpected diff (-want +got):\n%s", testStageRoot, tt.in, tt.period, diff)
		}
	}
}

func TestRetreiveTimesNoKey(t *testing.T) {
	testID := "TestRetreiveTimesNoKey"
	s := NewStage()
	err := s.RetreiveTimes(testStageRoot, "3")
	if err != nil {
		t.Errorf("%s(): raised unexpected error %v", testID, err)
	}
}
