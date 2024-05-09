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

"""Actions to regenerate Glazier tasklist."""

import os

from glazier.lib import constants
from glazier.lib import flags
from glazier.lib import logs
from glazier.lib import registry
from glazier.lib import winpe
from glazier.lib.actions import base
from glazier.lib.config import builder

from glazier.lib import buildinfo


logging = logs.logging


class RegenerateTasklist(base.BaseAction):
  """Regenerate Glazier tasklist."""

  def __init__(self):
    self._build_info = buildinfo.BuildInfo()

  def _PurgeTaskList(self):
    """Determines the location of the task list and erases it for regeneration."""
    location = constants.SYS_TASK_LIST
    if winpe.check_winpe():
      location = constants.WINPE_TASK_LIST
    logging.info('Using task list at %s', location)
    if os.path.exists(location):
      logging.info('Purging old task list.')
      try:
        os.remove(location)
      except OSError as e:
        raise base.ActionError() from e
    return location

  def Run(self):
    regen_run = registry.get_value('tasklist_regen', path=constants.REG_ROOT)
    if regen_run != 'True':
      task_list = self._PurgeTaskList()
      root_path = flags.CONFIG_ROOT_PATH.value or '/'
      try:
        b = builder.ConfigBuilder(self._build_info)
        b.Start(out_file=task_list, in_path=root_path)
      except builder.ConfigBuilderError as e:
        raise base.ActionError() from e
      registry.set_value('tasklist_regen', 'True', path=constants.REG_ROOT)

  def Validate(self):
    self._ListOfStringsValidator(self._args)
