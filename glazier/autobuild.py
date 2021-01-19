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
from typing import Optional

from absl import app
from absl import flags
from glazier.lib import buildinfo
from glazier.lib import constants
from glazier.lib import errors
from glazier.lib import logs
from glazier.lib import title
from glazier.lib import winpe
from glazier.lib.config import builder
from glazier.lib.config import runner

FLAGS = flags.FLAGS
flags.DEFINE_bool('preserve_tasks', False,
                  'Preserve the existing task list, if any.')

logging = logs.logging


def _LogFatal(msg: str,
              build_info: buildinfo.BuildInfo,
              code: int = 4000,
              exception: Optional[Exception] = None,
              collect: bool = True):
  """Log a fatal error and exit.

  This function handles all Glazier Exceptions by sequentially:
    - (Optional) Collecting logs to a zip folder on disk
    - Logging the full traceback to the debug log
    - Constructing the user-facing failure string, consisting of:
      * The message to accompany the failure
      * (Optional) The exception object, and if available, the file and line
         number of the root exception
      * The user-facing help message containing where to look for logs and
         where to go for further assistance.
    - Log the user-facing failure string
    - Exit Glazier with code 1

  Args:
    msg: The error message to accompany the failure.
    build_info: The active BuildInfo class.
    code: Error code to append to the failure message.
    exception: The exception object.
    collect: Whether to collect log files.
  """
  if collect:
    try:
      logs.Collect(os.path.join(build_info.CachePath(), r'\glazier_logs.zip'))
    except logs.LogError as e:
      logging.error('logs collection failed with %s', e)

  # Log the full traceback to _BUILD_LOG to assist in troubleshooting
  logging.debug(traceback.format_exc())

  string = f'{msg}\n\n'

  if exception:
    # Index 2 contains the traceback from the sys.exc_info() tuple
    trace = sys.exc_info()[2]
    if trace:
      # Index -1 contains the traceback object of the root exception
      trace_obj = traceback.extract_tb(trace)[-1]
      # The trace object contains the full file path, grab just the file name
      file = os.path.split(trace_obj.filename)[1]
      lineno = trace_obj.lineno

      string += f'Exception: {file}:{lineno}] {exception}\n\n'
    else:
      string += f'Exception] {exception}\n\n'

  build_log = constants.SYS_BUILD_LOG
  if winpe.check_winpe():
    build_log = constants.WINPE_BUILD_LOG

  string += (f'See {build_log} for more info. '
             f'Need help? Visit {constants.HELP_URI}#{code}')

  logging.fatal(string)
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
        # TODO: Migrate to GlazierError
        _LogFatal('Unable to remove task list', self._build_info, 4303, e)
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
          # TODO: Migrate to GlazierError
          _LogFatal('Failed to build the task list', self._build_info, 4302, e)

      try:
        r = runner.ConfigRunner(self._build_info)
        r.Start(task_list=task_list)
      except runner.ConfigRunnerError as e:
        # TODO: Migrate to GlazierError
        _LogFatal('Failed to execute the task list', self._build_info, 4303, e)
    except KeyboardInterrupt:
      logging.info('KeyboardInterrupt detected, exiting.')
      sys.exit(1)
    except errors.GlazierError as e:
      _LogFatal(e.message, self._build_info, e.code, e.exception)
    except Exception as e:  # pylint: disable=broad-except
      _LogFatal('Unknown Exception', self._build_info, 4000, e)


def main(unused_argv):
  AutoBuild().RunBuild()


if __name__ == '__main__':
  app.run(main)
