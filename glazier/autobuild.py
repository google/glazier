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
import re
import sys

# do not remove: internal placeholder 1

from absl import app
from glazier.lib import flags
from glazier.lib import interact
from glazier.lib import logs
from glazier.lib import ntp
from glazier.lib import title
from glazier.lib import winpe
from glazier.lib.config import builder
from glazier.lib.config import runner

from glazier.lib import buildinfo
from glazier.lib import constants
from glazier.lib import errors
from glazier.lib import terminator


logging = logs.logging


class Error(errors.GlazierError):
  pass


class BatteryStatusError(Error):
  """Error class for starting the imaging process while on battery."""

  def __init__(self):
    super().__init__(
        error_code=errors.ErrorCode.BATTERY_STATUS_ERROR,
        message=StripMargin('Imaging process started while on battery'),
    )


def StripMargin(message, deliminator='|'):
  """Function to strip the margins from multiline strings.

  Equivalent to the stripMargin function in scala:
  https://www.oreilly.com/library/view/scala-cookbook/9781449340292/ch01s03.html

  Args:
    message: message to strip margins from
    deliminator: character to mark the start of a margin (default pipe '|')

  Returns:
    stripped string
  """
  return re.sub(
      pattern=rf'^[ \t]+{re.escape(deliminator)}',
      repl='',
      string=message,
      flags=re.MULTILINE,
  )


def _SyncClock():
  """Sync BIOS clock to NTP, to avoid cert/date issues."""
  try:
    ntp.SyncClockToNtp(server=flags.NTP_SERVER.value)
  except ntp.NoNtpResponseError as e:
    logging.error('NTP synchronization failed ({}).'.format(str(e)))


def _CheckBattery(build_info):
  """Issue a warning if we are starting the imaging process on battery."""
  if not build_info.IsLaptop():
    return

  if build_info.IsOnBattery():
    timeout = 15
    message = f"""
    |                       !!!!! Warning !!!!!
    |
    |You are attempting to start the imaging process while on battery. It is
    |highly recommended that you plug your laptop in before continuing.
    |
    |This process will exit in {timeout} seconds automatically unless if you
    |choose to continue.
    |
    |  Continue anyways (y/n)?
    |"""
    result = interact.Keystroke(
        message=StripMargin(message), validator=r'^[yYnN].*', timeout=timeout
    )
    if not result or result.lower().startswith('n'):
      raise BatteryStatusError()


class AutoBuild(object):
  """The AutoBuild class manages the imaging process."""

  def __init__(self):
    self._build_info = buildinfo.BuildInfo()
    logs.Setup(self._build_info)

  def _SetupTaskList(self):
    """Determines the location of the task list and erases if necessary."""
    location = constants.SYS_TASK_LIST
    if winpe.check_winpe():
      location = constants.WINPE_TASK_LIST
    logging.debug('Using task list at %s', location)
    if not flags.PRESERVE_TASKS.value and os.path.exists(location):
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
      if winpe.check_winpe():
        _SyncClock()
        _CheckBattery(self._build_info)
      self._build_info.ImageID()
      self._build_info.BeyondCorp()

      task_list = self._SetupTaskList()

      if not os.path.exists(task_list):
        root_path = flags.CONFIG_ROOT_PATH.value or '/'
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
