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
"""Manages the execution of the local host task list."""

from __future__ import print_function

import sys

from glazier.lib import constants
from glazier.lib import download
from glazier.lib import policies
from glazier.lib import power
from glazier.lib.config import base
from glazier.lib.config import files


class ConfigRunnerError(base.ConfigError):
  pass


class ConfigRunner(base.ConfigBase):
  """Executes all steps from the installation task list."""

  def Start(self, task_list):
    self._task_list_path = task_list
    try:
      data = files.Read(self._task_list_path)
    except files.Error as e:
      raise ConfigRunnerError(e)
    self._ProcessTasks(data)

  def _PopTask(self, tasks):
    """Remove the first event from the task list and save new list to disk."""
    tasks.pop(0)
    try:
      files.Dump(self._task_list_path, tasks, mode='w')
      if not tasks:
        files.Remove(self._task_list_path)
    except files.Error as e:
      raise ConfigRunnerError(e)

  def _ProcessTasks(self, tasks):
    """Process the pending tasks list.

    Args:
      tasks: The list of pending tasks.

    Raises:
      ConfigRunnerError: failure to confirm verify_urls
    """
    if constants.FLAGS.verify_urls:
      dl = download.Download()
      for url in constants.FLAGS.verify_urls:
        if not dl.CheckUrl(url, [200], max_retries=-1):
          raise ConfigRunnerError('verify_urls failed for url %s' % url)

    while tasks:
      entry = tasks[0]['data']
      self._build_info.ActiveConfigPath(set_to=tasks[0]['path'])
      for element in entry:
        if element == 'policy':
          for line in entry['policy']:
            self._Policy(line)
        else:
          try:
            self._ProcessAction(element, entry[element])
          except base.ConfigError as e:
            raise ConfigRunnerError(e)
          except base.actions.RestartEvent as e:
            if e.task_list_path:
              self._task_list_path = e.task_list_path
            if not e.retry_on_restart:
              self._PopTask(tasks)
            power.Restart(e.timeout, str(e))
            sys.exit(0)
          except base.actions.ShutdownEvent as e:
            if e.task_list_path:
              self._task_list_path = e.task_list_path
            if not e.retry_on_restart:
              self._PopTask(tasks)
            power.Shutdown(e.timeout, str(e))
            sys.exit(0)
      self._PopTask(tasks)

  def _Policy(self, line):
    """Execute an imaging policy check.

    Args:
      line: The name of a supported imaging policy.

    Raises:
      ConfigRunnerError: An imaging policy has raised an exception.
    """
    try:
      check = getattr(policies, str(line))
      policy = check(build_info=self._build_info)
      policy.Verify()
    except AttributeError:
      raise ConfigRunnerError('Unknown imaging policy: %s' % str(line))
    except policies.ImagingPolicyException as e:
      raise ConfigRunnerError(str(e))
