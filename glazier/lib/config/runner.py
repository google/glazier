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

import sys

from glazier.lib import constants
from glazier.lib import events
from glazier.lib import logs
from glazier.lib import power
from glazier.lib.config import base as config_base
from glazier.lib.config import files

from glazier.lib import download
from glazier.lib import errors
from glazier.lib import policies

logging = logs.logging


class Error(errors.GlazierError):
  pass


class ConfigRunnerError(Error):

  def __init__(self):
    super().__init__(
        error_code=errors.ErrorCode.FAILED_TASK_LIST_RUN,
        message='Failed to execute the task list')


class UnknownPolicyError(Error):

  def __init__(self, policy: str):
    super().__init__(
        error_code=errors.ErrorCode.UNKNOWN_POLICY,
        message=f'Unknown imaging policy [{policy}]')


class CheckUrlError(Error):

  def __init__(self, url: str):
    super().__init__(
        error_code=errors.ErrorCode.FAILED_URL_VERIFICATION,
        message=f'Failed to verify url [{url}]')


class ConfigRunner(config_base.ConfigBase):
  """Executes all steps from the installation task list."""

  def Start(self, task_list):
    self._task_list_path = task_list
    try:
      data = files.Read(self._task_list_path)
    except files.Error as e:
      raise ConfigRunnerError() from e
    self._ProcessTasks(data)

  def _PopTask(self, tasks):
    """Remove the first event from the task list and save new list to disk."""
    tasks.pop(0)
    try:
      files.Dump(self._task_list_path, tasks, mode='w')
      if not tasks:
        files.Remove(self._task_list_path)
    except files.Error as e:
      raise ConfigRunnerError() from e

  def _ProcessTasks(self, tasks):
    """Process the pending tasks list.

    Args:
      tasks: The list of pending tasks.

    Raises:
      CheckUrlError: failure to confirm verify_urls.
      ConfigRunnerError: error encountered while running a task.
    """
    if constants.FLAGS.verify_urls:
      logging.info('Verifying %d URL(s)', len(constants.FLAGS.verify_urls))
      dl = download.Download()
      for url in constants.FLAGS.verify_urls:
        if not dl.CheckUrl(url, [200]):
          # TODO(b/236982963): Include the non-200 status code in the message.
          raise CheckUrlError(url=url)

    while tasks:
      self._build_info.ActiveConfigPath(set_to=tasks[0]['path'])
      entry = tasks[0]['data']
      for element in entry:
        if element == 'policy':
          for line in entry['policy']:
            self._Policy(line)
        else:
          try:
            self._ProcessAction(element, entry[element])
          except config_base.Error as e:
            raise ConfigRunnerError() from e
          except events.RestartEvent as e:
            if e.task_list_path:
              self._task_list_path = e.task_list_path
            if not e.retry_on_restart:
              self._PopTask(tasks)
            if e.pop_next:
              self._PopTask(tasks)
            power.Restart(e.timeout, str(e))
            sys.exit(0)
          except events.ShutdownEvent as e:
            if e.task_list_path:
              self._task_list_path = e.task_list_path
            if not e.retry_on_restart:
              self._PopTask(tasks)
            if e.pop_next:
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
    except AttributeError as e:
      raise UnknownPolicyError(policy=str(line)) from e
    except policies.ImagingPolicyException as e:
      raise ConfigRunnerError() from e
