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

// Package googet provides googet interoperability.
package googet

import (
	"errors"
	"fmt"
	"os"
	"regexp"
	"time"

	"github.com/google/glazier/go/helpers"
)

var (

	// Test Helpers
	funcExec = helpers.ExecWithVerify
)

// Config provides the ability to customize GooGet behavior.
type Config struct {
	GooGetExe string
	Timeout   time.Duration
}

// NewConfig generates a new Config object.
func NewConfig() *Config {
	return &Config{
		GooGetExe: os.Getenv("GooGetRoot") + `\googet.exe`,
		Timeout:   10 * time.Minute,
	}
}

func call(args []string, conf *Config) error {
	if conf == nil {
		conf = NewConfig()
	}

	_, err := funcExec(conf.GooGetExe, args, &conf.Timeout, nil)
	if err != nil && errors.Is(err, helpers.ErrTimeout) {
		return fmt.Errorf("execution timed out after %v", conf.Timeout)
	}
	return err
}

// Install installs a Googet package.
func Install(pkg, sources string, reinstall bool, conf *Config) error {
	if conf == nil {
		conf = NewConfig()
	}

	cmd := []string{"-noconfirm", "install"}
	if reinstall {
		cmd = append(cmd, "--reinstall")
	}
	if sources != "" {
		cmd = append(cmd, "--sources", sources)
	}
	cmd = append(cmd, pkg)

	return call(cmd, conf)
}

// PackageVersion attempts to retrieve the current version
// of the named package from the local system.
func PackageVersion(pkg string) (string, error) {
	timeout := 2 * time.Minute
	conf := NewConfig()

	out, err := funcExec(conf.GooGetExe, []string{"installed", pkg}, &timeout, nil)
	if err != nil {
		if errors.Is(err, helpers.ErrTimeout) {
			return "unknown", fmt.Errorf("execution timed out after %v", timeout)
		}
		return "unknown", err
	}
	ver := regexp.MustCompile(`[\d\.\-]+@[\d]+`).Find(out.Stdout)
	return string(ver), nil
}

// Remove removes a Googet package.
func Remove(pkg string, dbOnly bool, conf *Config) error {
	if conf == nil {
		conf = NewConfig()
	}

	args := []string{"-noconfirm", "remove"}
	if dbOnly {
		args = append(args, "-db_only")
	}
	args = append(args, pkg)

	return call(args, conf)
}

// RemoveRepo removes a Googet repository.
func RemoveRepo(repo string, conf *Config) error {
	if conf == nil {
		conf = NewConfig()
	}

	return call([]string{"rmrepo", repo}, conf)
}

// Update updates all googet packages.
func Update(conf *Config) error {
	if conf == nil {
		conf = NewConfig()
	}
	args := []string{"-noconfirm", "update"}

	return call(args, conf)
}
