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

"""Windows installation and configuration tool."""

import os
import sys
# do not remove: internal placeholder 1

from absl import app
from absl import flags
from glazier.lib import logs
from glazier.lib import title
from glazier.lib import winpe
from glazier.lib.config import builder
from glazier.lib.config import runner

from glazier.lib import buildinfo
from glazier.lib import constants
from glazier.lib import terminator

FLAGS = flags.FLAGS
flags.DEFINE_bool('preserve_tasks', False,
                  'Preserve the existing task list, if any.')

logging = logs.logging


class AutoBuild(object):
  """The AutoBuild class manages the imaging process."""

  def __init__(self):
    logs.Setup()
    self._build_info = buildinfo.BuildInfo()

  def _SetupTaskList(self):
    """Determines the location of the task list and erases if necessary."""
    location = constants.SYS_TASK_LIST
    if winpe.check_winpe():
      location = constants.WINPE_TASK_LIST
    logging.debug('Using task list at %s', location)
    if not FLAGS.preserve_tasks and os.path.exists(location):
      logging.debug('Purging old task list.')
      try:
        os.remove(location)
      except OSError as e:
        terminator.log_and_exit(self._build_info, e)
    return location

  def RunBuild(self):
    """Perform the build."""
    try:
      title.set_title()
      self._build_info.BeyondCorp()

      task_list = self._SetupTaskList()

      if not os.path.exists(task_list):
        root_path = FLAGS.config_root_path or '/'
        try:
          b = builder.ConfigBuilder(self._build_info)
          b.Start(out_file=task_list, in_path=root_path)
        except builder.ConfigBuilderError as e:
          terminator.log_and_exit(self._build_info, e)

      try:
        r = runner.ConfigRunner(self._build_info)
        r.Start(task_list=task_list)
      except runner.ConfigRunnerError as e:
        terminator.log_and_exit(self._build_info, e)

    except KeyboardInterrupt:
      logging.info('KeyboardInterrupt detected, exiting.')
      sys.exit(1)
    except Exception as e:  # pylint: disable=broad-except
      terminator.log_and_exit(self._build_info, e)


def main(unused_argv):
  AutoBuild().RunBuild()


if __name__ == '__main__':
  app.run(main)
