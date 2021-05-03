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

// Package tasks provides helpers for managing scheduled tasks.
package tasks

import (
	"errors"
	"strings"

	"github.com/capnspacehook/taskmaster"
)

var (
	// ErrTaskNotFound indicates a failure due to task resolution
	ErrTaskNotFound = errors.New("task not found")
	// ErrNotRegistered indicates that the querired Scheduled Task
	// is not registered in the Windows Task Scheduler
	ErrNotRegistered = errors.New("scheduled task is not registered")

	// Test Helpers
	fnGetTask = GetTask
)

func setEnabled(name string, enabled bool) error {
	task, err := GetTask(name)
	if err != nil {
		return err
	}
	defer task.Release()

	svc, err := taskmaster.Connect()
	if err != nil {
		return err
	}
	defer svc.Disconnect()

	task.Definition.Settings.Enabled = enabled
	_, err = svc.UpdateTask(task.Path, task.Definition)
	return err
}

// Disable disables a scheduled task.
func Disable(name string) error {
	return setEnabled(name, false)
}

// Enable enables a scheduled task.
func Enable(name string) error {
	return setEnabled(name, true)
}

// GetTask gathers details about a Windows Scheduled Task.
func GetTask(name string) (taskmaster.RegisteredTask, error) {
	svc, err := taskmaster.Connect()
	if err != nil {
		return taskmaster.RegisteredTask{}, err
	}
	defer svc.Disconnect()

	tasks, err := svc.GetRegisteredTasks()
	if err != nil {
		return taskmaster.RegisteredTask{}, err
	}
	defer tasks.Release()

	for _, t := range tasks {
		if strings.EqualFold(t.Name, name) {
			return t, nil
		}
	}

	return taskmaster.RegisteredTask{}, ErrNotRegistered
}

// TaskExists is a helper function that detects whether a scheduled task exists.
func TaskExists(name string) (bool, error) {
	task, err := fnGetTask(name)

	if err != nil && !errors.Is(err, ErrNotRegistered) {
		return false, err
	}

	if strings.EqualFold(task.Name, name) {
		return true, nil
	}

	return false, nil
}

// Delete attempts to delete a scheduled task.
func Delete(name string) error {
	svc, err := taskmaster.Connect()
	if err != nil {
		return err
	}
	defer svc.Disconnect()
	tasks, err := svc.GetRegisteredTasks()
	if err != nil {
		return err
	}
	defer tasks.Release()
	for _, t := range tasks {
		if strings.EqualFold(t.Name, name) {
			return svc.DeleteTask(t.Path)
		}
	}
	return ErrTaskNotFound
}
