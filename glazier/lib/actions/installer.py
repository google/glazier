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
from glazier.chooser import chooser
from glazier.lib import constants
from glazier.lib import log_copy
from glazier.lib import stage
from glazier.lib.actions import file_system
from glazier.lib.actions.base import ActionError
from glazier.lib.actions.base import BaseAction
from glazier.lib.actions.base import RestartEvent
from glazier.lib.actions.base import ValidationError
from gwinpy.registry import registry
import yaml


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
        raise ValidationError('Missing required field %s: %s' % (f, choice))

    for f in ['name', 'type', 'prompt']:
      self._TypeValidator(choice[f], str)

    self._TypeValidator(choice['options'], list)
    for opt in choice['options']:
      self._TypeValidator(opt, dict)

      if 'label' not in opt:
        raise ValidationError('Missing required field %s: %s' % ('label', opt))
      self._TypeValidator(opt['label'], str)

      if 'value' not in opt:
        raise ValidationError('Missing required field %s: %s' % ('value', opt))
      self._TypeValidator(opt['value'], (bool, str))

      if 'tip' in opt:
        self._TypeValidator(opt['tip'], str)
      if 'default' in opt:
        self._TypeValidator(opt['default'], bool)


class BuildInfoDump(BaseAction):
  """Dump build information to disk."""

  def Run(self):
    path = os.path.join(self._build_info.CachePath(), 'build_info.yaml')
    self._build_info.Serialize(path)


class BuildInfoSave(BaseAction):
  """Save build information to the registry."""

  def _WriteRegistry(self, input_keys):
    """Populates the registry with build_info settings for future reference.

    Args:
      input_keys: A dictionary of key/value pairs to be added to the registry.
    """
    reg = registry.Registry(root_key='HKLM')
    reg_root = constants.REG_ROOT
    for registry_key in input_keys:
      registry_value = input_keys[registry_key]
      reg.SetKeyValue(reg_root, registry_key, registry_value)
      logging.debug('Created registry value named %s with value %s.',
                    registry_key, registry_value)

  def Run(self):
    path = os.path.join(self._build_info.CachePath(), 'build_info.yaml')
    if os.path.exists(path):
      with open(path) as handle:
        input_config = yaml.safe_load(handle)
        self._WriteRegistry(input_config['BUILD'])
      os.remove(path)
    else:
      logging.debug('%s does not exist - skipping processing.', path)


class ExitWinPE(BaseAction):
  """Exit the WinPE environment to start host configuration."""

  def Run(self):
    cp = file_system.CopyFile([constants.WINPE_TASK_LIST,
                               constants.SYS_TASK_LIST], self._build_info)
    cp.Run()
    cp = file_system.CopyFile([constants.WINPE_BUILD_LOG,
                               constants.SYS_BUILD_LOG], self._build_info)
    cp.Run()
    raise RestartEvent(
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
    logging.debug('Sleeping for %d seconds.', duration)
    time.sleep(duration)

  def Validate(self):
    self._TypeValidator(self._args, list)
    if len(self._args) is not 1:
      raise ValidationError('Invalid args length: %s' % self._args)
    self._TypeValidator(self._args[0], int)


class StartStage(BaseAction):
  """Start a new stage of the installation."""

  def Run(self):
    try:
      stage.set_stage(int(self._args[0]))
    except stage.Error as e:
      raise ActionError(str(e))

  def Validate(self):
    self._TypeValidator(self._args, list)
    if len(self._args) != 1:
      raise ValidationError('Invalid args length: %s' % self._args)
    self._TypeValidator(self._args[0], int)
