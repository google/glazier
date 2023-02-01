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
	"fmt"
	"strings"
	"time"

	"github.com/capnspacehook/taskmaster"
)

var (
	// ErrTaskNotFound indicates a failure due to task resolution
	ErrTaskNotFound = errors.New("task not found")
	// ErrNotRegistered indicates that the querired Scheduled Task
	// is not registered in the Windows Task Scheduler
	ErrNotRegistered = errors.New("scheduled task is not registered")
)

// TaskInfo describes a registered task using data from taskmaster.RegisteredTask.
type TaskInfo struct {
	Name           string
	State          taskmaster.TaskState
	LastTaskResult taskmaster.TaskResult
	NextRunTime    time.Time
	LastRunTime    time.Time
}

func setEnabled(name string, enabled bool) error {
	svc, err := taskmaster.Connect()
	if err != nil {
		return fmt.Errorf("taskmaster.Connect: %w", err)
	}
	defer svc.Disconnect()

	tasks, err := svc.GetRegisteredTasks()
	if err != nil {
		return fmt.Errorf("svc.GetRegisteredTasks: %w", err)
	}
	defer tasks.Release()

	for _, t := range tasks {
		if strings.EqualFold(t.Name, name) {
			t.Definition.Settings.Enabled = enabled
			_, err = svc.UpdateTask(t.Path, t.Definition)
			return err
		}
	}
	return ErrTaskNotFound
}

// names must start with "\"
func formatName(name string) string {
	if !strings.HasPrefix(name, `\`) {
		name = `\` + name
	}
	return name
}

func getTask(name string) (TaskInfo, error) {
	task := TaskInfo{}
	svc, err := taskmaster.Connect()
	if err != nil {
		return task, fmt.Errorf("taskmaster.Connect: %w", err)
	}
	defer svc.Disconnect()

	tmTask, err := svc.GetRegisteredTask(name)
	if err != nil {
		return task, fmt.Errorf("svc.GetRegisteredTask: %w", err)
	}
	defer tmTask.Release()
	// Convert the svctask info to a helpers struct so we can release TaskMaster handles.
	task.Name = tmTask.Name
	task.State = tmTask.State
	task.LastTaskResult = tmTask.LastTaskResult
	task.NextRunTime = tmTask.NextRunTime
	task.LastRunTime = tmTask.LastRunTime

	return task, nil
}

// Fetch fetches a scheduled tasks state.
func Fetch(name string) (TaskInfo, error) {
	name = formatName(name)
	return getTask(name)
}

// Disable disables a scheduled task.
func Disable(name string) error {
	return setEnabled(name, false)
}

// Enable enables a scheduled task.
func Enable(name string) error {
	return setEnabled(name, true)
}

func taskMatcher(name string, tasks taskmaster.RegisteredTaskCollection) bool {
	for _, t := range tasks {
		if strings.EqualFold(t.Name, name) {
			return true
		}
	}
	return false
}

// TaskExists is a helper function that detects whether a scheduled task exists.
func TaskExists(name string) (bool, error) {
	svc, err := taskmaster.Connect()
	if err != nil {
		return false, fmt.Errorf("taskmaster.Connect: %w", err)
	}
	defer svc.Disconnect()

	tasks, err := svc.GetRegisteredTasks()
	if err != nil {
		return false, fmt.Errorf("svc.GetRegisteredTasks: %w", err)
	}
	defer tasks.Release()

	return taskMatcher(name, tasks), nil
}

// Create attempts to create a scheduled task.
//
// Set common defaults for name and user to reduce the amount of required args.
//
// Example taskmaster.Trigger that creates a new task on startup with a two minute delay:
//
//	taskmaster.BootTrigger{
//	  TaskTrigger: taskmaster.TaskTrigger{
//			 Enabled: true,
//			 ID:      "startup",
//		 },
//		 Delay: period.NewHMS(0, 2, 0),
//	},
func Create(id, path, args, name, user string, trigger taskmaster.Trigger) error {
	svc, err := taskmaster.Connect()
	if err != nil {
		return fmt.Errorf("taskmaster.Connect: %w", err)
	}
	defer svc.Disconnect()

	def := svc.NewTaskDefinition()
	def.AddAction(taskmaster.ExecAction{
		ID:   id,
		Path: path,
		Args: args,
	})
	def.Principal.RunLevel = taskmaster.TASK_RUNLEVEL_HIGHEST
	if user == "" {
		user = "SYSTEM"
	}
	def.Principal.UserID = user
	def.AddTrigger(trigger)

	if name == "" {
		name = id
	}
	task, ok, err := svc.CreateTask(`\`+name, def, true)
	if err != nil {
		return fmt.Errorf("svc.CreateTask: %w", err)
	}
	if !ok {
		return errors.New("unable to register task")
	}
	task.Release()

	return nil
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

// Start attempts to start a scheduled task. This helper does not follow the running task or wait
// for execution to complete.
func Start(name string) error {
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
			_, err := t.Run()
			return err
		}
	}
	return ErrTaskNotFound
}
