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
	"strings"
	"time"

	"github.com/google/logger"
	"github.com/google/glazier/go/helpers"
)

var (
	// Test Helpers
	funcExec = helpers.Exec
)

// Config provides the ability to customize GooGet behavior.
type Config struct {
	GooGetExe  string
	ExecConfig helpers.ExecConfig
}

// NewConfig generates a new Config object.
func NewConfig() *Config {
	timeout := 10 * time.Minute
	return &Config{
		GooGetExe: os.Getenv("GooGetRoot") + `\googet.exe`,
		ExecConfig: helpers.ExecConfig{
			Timeout:  &timeout,
			Verifier: helpers.NewExecVerifier(),
		},
	}
}

func call(args []string, conf *Config) error {
	if conf == nil {
		conf = NewConfig()
	}

	res, err := funcExec(conf.GooGetExe, args, &conf.ExecConfig)
	logger.Infof("Executing: %s %v", conf.GooGetExe, args)
	if err != nil {
		logger.Errorf("googet stdout: %v", string(res.Stdout))
		logger.Errorf("googet stderr: %v", string(res.Stderr))
		if errors.Is(err, helpers.ErrTimeout) {
			return fmt.Errorf("execution timed out after %v", conf.ExecConfig.Timeout)
		}
	}
	return err
}

// AddRepo adds a googet repository to the local system.
func AddRepo(name, url string, conf *Config) error {
	if conf == nil {
		conf = NewConfig()
	}

	if name == "" || url == "" {
		return errors.New("must specify name and url")
	}

	return call([]string{"addrepo", name, url}, conf)
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

// Clean cleans the Googet cache directory.
func Clean(conf *Config) error {
	if conf == nil {
		conf = NewConfig()
	}

	cmd := []string{"-noconfirm", "clean"}
	return call(cmd, conf)
}

// Package represents a GooGet package.
type Package struct {
	Name    string
	Version string
}

// Installed lists installed package(s).
func Installed(initial string, conf *Config) ([]Package, error) {
	if conf == nil {
		conf = NewConfig()
	}

	p := []Package{}
	args := []string{"installed", initial}
	res, err := funcExec(conf.GooGetExe, args, &conf.ExecConfig)
	if err != nil {
		return p, err
	}
	lines := strings.Split(string(res.Stdout), "\n")
	for i, r := range lines {
		r = strings.TrimSpace(r)
		if i == 0 || r == "" {
			continue
		}
		dat := strings.Fields(r)
		if len(dat) < 2 {
			logger.Errorf("unable to parse googet output %v", r)
			continue
		}
		p = append(p, Package{
			Name:    dat[0],
			Version: dat[1],
		})
	}

	return p, nil
}

// Repo represents a googet repository configuration.
type Repo struct {
	Name string
	URL  string
}

// ListRepos lists the googet repos configured on the local system.
func ListRepos(conf *Config) ([]Repo, error) {
	if conf == nil {
		conf = NewConfig()
	}

	repos := []Repo{}
	args := []string{"listrepos"}
	res, err := funcExec(conf.GooGetExe, args, &conf.ExecConfig)
	if err != nil {
		return repos, err
	}

	lines := strings.Split(string(res.Stdout), "\n")
	for i, r := range lines {
		r = strings.TrimSpace(r)
		if i == 0 || r == "" {
			continue
		}
		if !strings.Contains(r, "http") { // skip repo file lines
			continue
		}
		dat := strings.SplitN(r, ":", 2)
		if len(dat) < 2 {
			logger.Errorf("unable to parse googet output %v", r)
			continue
		}
		repos = append(repos, Repo{
			Name: strings.TrimSpace(dat[0]),
			URL:  strings.TrimSpace(dat[1]),
		})
	}
	return repos, nil
}

// PackageVersion attempts to retrieve the current version
// of the named package from the local system.
func PackageVersion(pkg string) (string, error) {
	conf := NewConfig()

	out, err := funcExec(conf.GooGetExe, []string{"installed", pkg}, &conf.ExecConfig)
	if err != nil {
		if errors.Is(err, helpers.ErrTimeout) {
			return "unknown", fmt.Errorf("execution timed out after %v", conf.ExecConfig.Timeout)
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
