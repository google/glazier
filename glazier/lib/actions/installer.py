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
"""Actions for managing the installer."""

import logging
import os
import time
# do not remove: internal placeholder 1
from glazier.chooser import chooser
from glazier.lib import events
from glazier.lib import log_copy
from glazier.lib import registry
from glazier.lib import stage
from glazier.lib.actions import file_system
from glazier.lib.actions.base import ActionError
from glazier.lib.actions.base import BaseAction
from glazier.lib.actions.base import ValidationError
import yaml

from glazier.lib import constants


class AddChoice(BaseAction):
  """Add a pending question for display in the UI."""

  def _Setup(self):
    self._realtime = True

  def Run(self):
    self._build_info.AddChooserOption(self._args)

  def Validate(self):
    choice = self._args
    self._TypeValidator(choice, dict)

    for f in ['name', 'type', 'prompt', 'options']:
      if f not in choice:
        raise ValidationError(f'Missing required field {f}: {choice}')

    for f in ['name', 'type', 'prompt']:
      self._TypeValidator(choice[f], str)

    self._TypeValidator(choice['options'], list)
    for opt in choice['options']:
      self._TypeValidator(opt, dict)

      if 'label' not in opt:
        raise ValidationError(f'Missing required field "label": {opt}')
      self._TypeValidator(opt['label'], str)

      if 'value' not in opt:
        raise ValidationError(f'Missing required field "value": {opt}')
      self._TypeValidator(opt['value'], (bool, str))

      if 'tip' in opt:
        self._TypeValidator(opt['tip'], str)
      if 'default' in opt:
        self._TypeValidator(opt['default'], bool)


class BuildInfoDump(BaseAction):
  """Dump build information to disk."""

  def Run(self):
    path = os.path.join(constants.SYS_CACHE, 'build_info.yaml')
    logging.debug('Dumping build information to file: %s', path)
    self._build_info.Serialize(path)


class BuildInfoSave(BaseAction):
  """Save build information to the registry."""

  def _WriteRegistry(self, reg_values):
    """Populates the registry with build_info settings for future reference.

    Args:
      reg_values: A dictionary of key/value pairs to be added to the registry.
    """
    for value_name in reg_values:
      key_path = constants.REG_ROOT
      value_data = reg_values[value_name]
      if 'TIMER_' in value_name:
        key_path = r'{0}\{1}'.format(constants.REG_ROOT, 'Timers')
      try:
        registry.set_value(value_name, value_data, 'HKLM', key_path)
      except registry.Error as e:
        raise ActionError() from e

  def Run(self):
    path = os.path.join(constants.SYS_CACHE, 'build_info.yaml')
    if os.path.exists(path):
      with open(path) as handle:
        input_config = yaml.safe_load(handle)
        self._WriteRegistry(input_config['BUILD'])
      os.remove(path)
    else:
      logging.debug('%s does not exist - skipped processing.', path)


class ChangeServer(BaseAction):
  """Move to a different Glazier server."""

  def _Setup(self):
    self._realtime = True

  def Run(self):
    self._build_info.ConfigServer(set_to=self._args[0])
    self._build_info.ActiveConfigPath(set_to=self._args[1])
    raise events.ServerChangeEvent('Action triggering server change.')

  def Validate(self):
    self._ListOfStringsValidator(self._args, 2)


class ExitWinPE(BaseAction):
  """Exit the WinPE environment to start host configuration."""

  def Run(self):
    cp = file_system.CopyFile(
        [constants.WINPE_TASK_LIST, constants.SYS_TASK_LIST], self._build_info)
    cp.Run()
    cp = file_system.CopyFile(
        [constants.WINPE_BUILD_LOG, constants.SYS_BUILD_LOG], self._build_info)
    cp.Run()
    raise events.RestartEvent(
        'Leaving WinPE', timeout=10, task_list_path=constants.SYS_TASK_LIST)


class LogCopy(BaseAction):
  """Upload build logs for collection."""

  def Run(self):
    file_name = str(self._args[0])
    share = None
    if len(self._args) > 1:
      share = str(self._args[1])
    logging.debug('Found log copy event for file %s to %s.', file_name, share)
    copier = log_copy.LogCopy()

    # EventLog
    try:
      copier.EventLogCopy(file_name)
    except log_copy.LogCopyError as e:
      logging.warning('Unable to complete log copy to EventLog. %s', e)
    # CIFS
    if share:
      try:
        copier.ShareCopy(file_name, share)
      except log_copy.LogCopyError as e:
        logging.warning('Unable to complete log copy via CIFS. %s', e)

  def Validate(self):
    self._ListOfStringsValidator(self._args, 1, 2)


class ShowChooser(BaseAction):
  """Show the Chooser UI."""

  def Run(self):
    ui = chooser.Chooser(options=self._build_info.GetChooserOptions())
    ui.Display()
    responses = ui.Responses()
    self._build_info.StoreChooserResponses(responses)
    self._build_info.FlushChooserOptions()

  def _Setup(self):
    self._realtime = True


class Sleep(BaseAction):
  """Pause the installer."""

  def Run(self):
    duration = int(self._args[0])
    converted_time = time.strftime('%H:%M:%S', time.gmtime(duration))

    if len(self._args) > 1:
      logging.info('Sleeping for %s (%s).', converted_time, str(self._args[1]))
    else:
      logging.info('Sleeping for %s before continuing...', converted_time)
    time.sleep(duration)

  def Validate(self):
    self._TypeValidator(self._args, list)
    if len(self._args) > 2:
      raise ValidationError(f'Invalid args length: {len(self._args)}')
    self._TypeValidator(self._args[0], int)
    if len(self._args) > 1:
      self._TypeValidator(self._args[1], str)


class StartStage(BaseAction):
  """Start a new stage of the installation."""

  def Run(self):
    try:
      stage.set_stage(int(self._args[0]))
      # Terminal stages exit immediately; the build should be complete.
      if len(self._args) > 1 and self._args[1]:
        stage.exit_stage(int(self._args[0]))
    except stage.Error as e:
      raise ActionError() from e

  def Validate(self):
    self._TypeValidator(self._args, list)
    if len(self._args) > 2:
      raise ValidationError(f'Invalid args length: {len(self._args)}')
    self._TypeValidator(self._args[0], int)
    if len(self._args) > 1:
      self._TypeValidator(self._args[1], bool)
