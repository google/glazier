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
import traceback
from typing import Optional, Text

from absl import app
from absl import flags
from glazier.lib import buildinfo
from glazier.lib import constants
from glazier.lib import logs
from glazier.lib import title
from glazier.lib import winpe
from glazier.lib.config import builder
from glazier.lib.config import runner

FLAGS = flags.FLAGS
flags.DEFINE_bool('preserve_tasks', False,
                  'Preserve the existing task list, if any.')

logging = logs.logging

_FAILURE_MSG = ('%s\n\nInstaller cannot continue.')


def _LogFatal(msg: Text,
              build_info: buildinfo.BuildInfo,
              code: Optional[int] = None,
              collect: bool = True):
  """Log a fatal error and exit.

  Args:
    msg: The error message to accompany the failure.
    build_info: The active BuildInfo class.
    code: Error code to append to the failure message.
    collect: Whether to collect log files.
  """
  string = _FAILURE_MSG
  if code:
    string = _FAILURE_MSG + '#' + str(code)
  logging.fatal(string, msg)
  sys.exit(1)


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
        _LogFatal('Unable to remove task list.  %s' % e, self._build_info)
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
          _LogFatal(str(e), self._build_info)

      try:
        r = runner.ConfigRunner(self._build_info)
        r.Start(task_list=task_list)
      except runner.ConfigRunnerError as e:
        _LogFatal(str(e), self._build_info)
    except KeyboardInterrupt:
      logging.info('KeyboardInterrupt detected, exiting.')
      sys.exit(1)
    except Exception:  # pylint: disable=broad-except
      _LogFatal(traceback.format_exc(), self._build_info, 4000)


def main(unused_argv):
  AutoBuild().RunBuild()


if __name__ == '__main__':
  app.run(main)
