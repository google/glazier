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

// Package helpers provides miscellaneous helper functionality to other diagnose_me packages.
package helpers

import (
	"errors"
	"io"
	"os"
	"regexp"
	"strings"
	"syscall"
	"time"
)

// ExecResult holds the output from a subprocess execution.
type ExecResult struct {
	Stdout       []byte
	Stderr       []byte
	ExitCode     int
	ExitErr      error
	ProcessTimer time.Duration
}

// ExecError holds errors and output from failed subprocess executions.
type ExecError struct {
	errmsg     string
	procresult ExecResult
}

// ExecConfig provides flexible execution configuration.
type ExecConfig struct {
	// A verifier, if specified, will attempt to verify the subprocess output and return an error if problems are detected.
	Verifier *ExecVerifier

	// A timeout will kill the subprocess if it doesn't execute within the duration. Leave nil to disable timeout.
	Timeout *time.Duration

	// If RetryCount is non-zero, Exec will attempt to retry a failed execution (one which returns err). Executions will retry
	// every RetryInterval. Combine with a Verifier to retry until certain conditions are met.
	RetryCount    int
	RetryInterval *time.Duration

	SpAttr *syscall.SysProcAttr

	// WriteStdOut and WriteStdErr will receive a copy of the child process's output and/or error streams as they're written.
	// If nil, output is returned at the end of execution via the ExecResult.
	WriteStdOut io.Writer
	WriteStdErr io.Writer
}

var (
	// ErrExitCode indicates an exit-code related failure
	ErrExitCode = errors.New("produced invalid exit code")
	// ErrStdErr indicates an problem with an executables stderr content
	ErrStdErr = errors.New("problem detected in error output")
	// ErrStdOut indicates an problem with an executables stdout content
	ErrStdOut = errors.New("problem detected in output")
	// ErrTimeout indicates a timeout related failure
	ErrTimeout = errors.New("time limit reached, killed executable")
	// ErrUnsupported indicates an unsupported function call
	ErrUnsupported = errors.New("unsupported function call")

	// PsPath contains the full path to Windows Powershell.
	PsPath = os.ExpandEnv("${windir}\\System32\\WindowsPowerShell\\v1.0\\powershell.exe")

	// Test helpers
	fnSleep = time.Sleep
)

// Satisfies the Error interface and returns the simple error string associated with the execution.
func (e ExecError) Error() string {
	return e.errmsg
}

// Result returns any information that could be captured from the subprocess that was executed.
func (e ExecError) Result() ExecResult {
	return e.procresult
}

// ExecVerifier provides checks against executable results.
//
// SuccessCodes specifies which exit codes are considered successful.
// StdErrMatch, if present, attempts to match specific strings in stderr, and if found, treats them as a failure.
// StdOutMatch, if present, attempts to match specific strings in stdout, and if found, treats them as a failure.
type ExecVerifier struct {
	SuccessCodes []int
	StdOutMatch  *regexp.Regexp
	StdErrMatch  *regexp.Regexp
}

// NewExecVerifier applys the default values to an ExecVerifier.
func NewExecVerifier() *ExecVerifier {
	return &ExecVerifier{
		SuccessCodes: []int{0},
	}
}

// ContainsString returns true if a string is in slice and false otherwise.
func ContainsString(a string, slice []string) bool {
	for _, b := range slice {
		if a == b {
			return true
		}
	}
	return false
}

// PathExists returns whether the given file or directory exists or not
func PathExists(path string) (bool, error) {
	if strings.TrimSpace(path) == "" {
		return false, errors.New("path cannot be empty")
	}

	_, err := os.Stat(path)
	if err == nil {
		return true, nil
	}
	if !errors.Is(err, os.ErrNotExist) {
		return false, err
	}
	return false, nil
}

// StringInSlice checks if a slice contains a string.
func StringInSlice(e string, s []string) bool {
	for _, a := range s {
		if a == e {
			return true
		}
	}
	return false
}

// StringToSlice converts a comma separated string to a slice.
func StringToSlice(s string) []string {
	if strings.TrimSpace(s) == "" {
		return nil
	}
	a := strings.Split(s, ",")
	for i, item := range a {
		a[i] = strings.TrimSpace(item)
	}
	return a
}

// StringToMap converts a comma separated string to a map.
func StringToMap(s string) map[string]bool {
	m := map[string]bool{}
	if s != "" {
		for _, item := range strings.Split(s, ",") {
			m[strings.TrimSpace(item)] = true
		}
	}
	return m
}
