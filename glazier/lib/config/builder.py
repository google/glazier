# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Manages the initial processing of build.yaml files.

## Overview

The Config Builder is responsible for compiling a custom installation task list
for the local host.  It traces through all yaml configuration files linked to
the root config, and stores any commands that are determined applicable by
pinning (or lack thereof).

The end result of running ConfigBuilder is a single ordered list of tasks to
be performed when installing the host.

## Use

Start is the main entry point for the class.  It expects a path to a
configuration directory and a filename (the base build.yaml).

## Include Logic

Yaml files can refer to one another via the include directive.  Each sub-yaml
is treated identically to the base file, following the exact same logic.  The
include directive calls Start on each included file, completing that file
top-to-bottom before returning to the caller.

BuildInfo tracks our position in the directory tree.  Additional levels
(includes in sub-directories) are pushed onto the ActiveConfigPath while we
process the include.  At the end of processing the stack is popped, returning us
to our previous level.  This allows us to reference other files relative to the
location of the active config.
"""

import copy
# do not remove: internal placeholder 1
from glazier.lib import buildinfo
from glazier.lib.config import base
from glazier.lib.config import files

from glazier.lib import actions
from glazier.lib import download
from glazier.lib import errors

_ALLOW_IN_TEMPLATE = [
    'include',
    'template',
    'execute',
    'policy',
] + dir(actions)
_ALLOW_IN_CONTROL = _ALLOW_IN_TEMPLATE + ['pin']


class Error(errors.GlazierError):
  pass


class ConfigBuilderError(Error):

  def __init__(self):
    super().__init__(
        error_code=errors.ErrorCode.FAILED_TASK_LIST_BUILD,
        message='Failed to build the task list')


class SysInfoError(Error):

  def __init__(self):
    super().__init__(
        error_code=errors.ErrorCode.SYS_INFO,
        message='Error gathering system information')


class UnknownActionError(Error):

  def __init__(self, action: str):
    super().__init__(
        error_code=errors.ErrorCode.UNKNOWN_ACTION,
        message=f'Unknown imaging action [{action}]')


class ConfigBuilder(base.ConfigBase):
  """Builds the complete task list for the installation."""

  def Start(self, out_file, in_path, in_file='build.yaml'):
    """Start parsing configuration files.

    Args:
      out_file: The location to store the compiled config data.
      in_path: The path to the root configuration file.
      in_file: The root configuration file name.
    """
    self._task_list = []
    while True:
      try:
        self._Start(in_path, in_file)
        break
      except actions.ServerChangeEvent:
        in_path = ''  # restart with a fresh path
    try:
      files.Dump(out_file, self._task_list, mode='a')
    except files.Error as e:
      raise ConfigBuilderError() from e

  def _Start(self, conf_path, conf_file):
    """Pull and process a config file.

    Args:
      conf_path: The path to the config below root.
      conf_file: A named config file, normally build.yaml.
    """
    self._build_info.ActiveConfigPath(append=conf_path.rstrip('/'))
    try:
      path = download.PathCompile(self._build_info, file_name=conf_file)
      yaml_config = files.Read(path)
    except (files.Error, buildinfo.Error) as e:
      raise ConfigBuilderError() from e
    timer_start = 'start_{}_{}'.format(conf_path.rstrip('/'), conf_file)
    active_path = copy.deepcopy(self._build_info.ActiveConfigPath())
    self._task_list.append({
        'path': active_path,
        'data': {
            'SetTimer': [timer_start]
        }
    })
    controls = yaml_config['controls']
    try:
      for control in controls:
        if 'pin' not in control or self._MatchPin(control['pin']):
          self._StoreControls(control, yaml_config.get('templates'))
    finally:
      # close out any timers before raising a server change
      timer_stop = 'stop_{}_{}'.format(conf_path.rstrip('/'), conf_file)
      self._task_list.append({
          'path': active_path,
          'data': {
              'SetTimer': [timer_stop]
          }
      })
    self._build_info.ActiveConfigPath(pop=True)

  def _MatchPin(self, pins):
    """Check all pin entries for a mismatch.

    Pins can mismatch either by the matching setting being omitted or by
    matching an exclusion (!).

    Example:
      pins: ['os', ['win7', 'win8']]

      * Will match os = win7 or os = win8.
      * Will fail to match os = '2012r2'.
      * Will match model = 'vmware' (because model is not pinned).

    Example 2:
      pins: ['os', ['!win7']]

      * Will match os = win8 or os = 2012r2.
      * Will fail to match os = 'win7'.
      * Will match model = 'vmware' (because model is not pinned).

    Args:
      pins: a list of all applicable pin names and acceptable values

    Returns:
      True if this host passes all pin checks. False if the host fails a match.
    """
    for pin in pins:
      try:
        if not self._build_info.BuildPinMatch(pin, pins[pin]):
          return False
      except buildinfo.Error as e:
        raise SysInfoError() from e
    return True

  def _StoreControls(self, control, templates):
    """Process all of the possible sub-sections of a main control section.

    Args:
      control: The data from this control subsection.
      templates: Any templates declared in the current config.

    Raises:
      UnknownActionError: Attempt to process an unknown command element.
    """
    for element in control:
      if element == 'pin':
        continue
      elif element == 'template':
        for template in control['template']:
          self._StoreControls(templates[template], templates)
      elif element == 'include':
        for sub_inc in control['include']:
          self._Start(conf_path=sub_inc[0], conf_file=sub_inc[1])
      elif element in _ALLOW_IN_CONTROL:
        if self._IsRealtimeAction(element, control[element]):
          self._ProcessAction(element, control[element])
        else:
          self._task_list.append({
              'path': copy.deepcopy(self._build_info.ActiveConfigPath()),
              'data': {element: control[element]}
          })
      else:
        raise UnknownActionError(str(element))
