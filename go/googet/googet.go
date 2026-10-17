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
	"path/filepath"
	"regexp"
	"runtime"
	"strconv"
	"strings"
	"time"

	"github.com/google/deck"
	"github.com/google/glazier/go/helpers"
	"github.com/google/glazier/go/registry"
)

const (
	// envVar is the environment variable that holds the GooGet root directory.
	envVar = "GooGetRoot"
	// machineEnvironment is the registry key of the machine-wide environment
	// variables, where the GooGet installer stores GooGetRoot.
	machineEnvironment = `SYSTEM\CurrentControlSet\Control\Session Manager\Environment`
)

var (
	// Test Helpers
	funcExec = helpers.Exec
	// funcMachineGooGetRoot returns the GooGetRoot value of the machine-wide
	// environment, which only administrators can change.
	funcMachineGooGetRoot = func() (string, error) { return registry.GetString(machineEnvironment, envVar) }
)

// Config provides the ability to customize GooGet behavior.
type Config struct {
	GooGetExe string
	// Root is the GooGet root directory that commands pass to googet.exe with
	// -root. If Root is empty, googet.exe reads the GooGetRoot variable of the
	// process environment.
	Root       string
	ExecConfig helpers.ExecConfig
}

// NewConfig generates a new Config object.
func NewConfig() *Config {
	timeout := 10 * time.Minute
	root := gooGetRoot()
	return &Config{
		GooGetExe: gooGetExe(root),
		Root:      root,
		ExecConfig: helpers.ExecConfig{
			Timeout:  &timeout,
			Verifier: helpers.NewExecVerifier(),
		},
	}
}

// gooGetRoot returns the GooGet root directory. It prefers the machine-wide
// GooGetRoot value in the registry, which only administrators can change, over
// the environment of the process. It returns "" if neither names an absolute
// directory.
func gooGetRoot() string {
	root, err := funcMachineGooGetRoot()
	if err != nil || !isAbsRoot(root) {
		root = os.Getenv(envVar)
	}
	if !isAbsRoot(root) {
		return ""
	}
	return root
}

// gooGetExe returns the path of googet.exe in root. It returns "" if root is
// empty, so that commands fail instead of running a googet.exe relative to the
// current drive.
func gooGetExe(root string) string {
	if root == "" {
		return ""
	}
	return root + `\googet.exe`
}

// isAbsRoot reports whether root names an absolute directory. A relative root
// would run a googet.exe from the current directory or drive.
// filepath.IsAbs knows drive letters only on Windows.
func isAbsRoot(root string) bool {
	return root != "" && (runtime.GOOS != "windows" || filepath.IsAbs(root))
}

// execGooGet runs googet.exe with args. It passes conf.Root with -root, so
// that googet.exe uses the root that NewConfig resolved instead of the
// GooGetRoot variable of the process environment.
func execGooGet(args []string, conf *Config) (helpers.ExecResult, error) {
	if conf.Root != "" {
		args = append([]string{"-root", conf.Root}, args...)
	}
	return funcExec(conf.GooGetExe, args, &conf.ExecConfig)
}

func call(args []string, conf *Config) error {
	if conf == nil {
		conf = NewConfig()
	}

	res, err := execGooGet(args, conf)
	deck.Infof("Executing: %s %v", conf.GooGetExe, args)
	if err != nil {
		deck.Errorf("googet stdout: %v", string(res.Stdout))
		deck.Errorf("googet stderr: %v", string(res.Stderr))
		if errors.Is(err, helpers.ErrTimeout) {
			return fmt.Errorf("execution timed out after %v", conf.ExecConfig.Timeout)
		}
	}
	return err
}

// AddRepo adds a googet repository to the local system.
func AddRepo(name, url string, priority int, conf *Config) error {
	if conf == nil {
		conf = NewConfig()
	}
	if name == "" || url == "" {
		return errors.New("must specify name and url")
	}

	args := []string{"addrepo"}
	if priority != 0 {
		args = append(args, "--priority", strconv.Itoa(priority))
	}
	args = append(args, name, url)
	return call(args, conf)
}

// Install installs a Googet package.
func Install(pkg, sources string, reinstall bool, dbOnly bool, conf *Config) error {
	if conf == nil {
		conf = NewConfig()
	}

	cmd := []string{"-noconfirm", "install"}
	if reinstall {
		cmd = append(cmd, "-reinstall")
	}
	if sources != "" {
		cmd = append(cmd, "-sources", sources)
	}
	if dbOnly {
		cmd = append(cmd, "-db_only")
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
	res, err := execGooGet(args, conf)
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
			deck.Errorf("unable to parse googet output %v", r)
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
	res, err := execGooGet(args, conf)
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
			deck.Errorf("unable to parse googet output %v", r)
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

	out, err := execGooGet([]string{"installed", pkg}, conf)
	if err != nil {
		if errors.Is(err, helpers.ErrTimeout) {
			return "unknown", fmt.Errorf("execution timed out after %v", conf.ExecConfig.Timeout)
		}
		if strings.Contains(string(out.Stdout), "No package matching filter") {
			return "unknown", nil
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
