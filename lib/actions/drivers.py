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

"""Actions for managing device drivers."""

import logging
import os
from glazier.lib import constants
from glazier.lib import file_util
from glazier.lib.actions.base import ActionError
from glazier.lib.actions.base import BaseAction
from glazier.lib.actions.base import ValidationError
from glazier.lib.actions.files import Execute
from glazier.lib.actions.files import Get


class DriverWIM(BaseAction):
  """Downloads file and verifies extension.

  File is downloaded and processed based on supported file extension.
  file can then be processed to be used by dism commands.

  Method can be expanded to access and process other formats.
  Also can be used to process multiple files.

  Raises:
    ActionError: Call with unsupported file type.
  """
  FILE_EXT_SUPPORTED = ['.wim']

  def Run(self):
    for wim in self._args:
      dst = str(wim[1])
      file_ext = os.path.splitext(dst)[1]

      if file_ext not in self.FILE_EXT_SUPPORTED:
        raise ActionError('Unsupported driver file format %s.' % dst)

      g = Get([wim], self._build_info)
      g.Run()

      logging.info('Found WIM file, processing drivers using DISM.')
      self._ProcessWim(dst)

  def Validate(self):
    self._TypeValidator(self._args, list)
    for cmd_arg in self._args:
      self._TypeValidator(cmd_arg, list)
      if not 2 <= len(cmd_arg) <= 3:
        raise ValidationError('Invalid args length: %s' % cmd_arg)
      self._TypeValidator(cmd_arg[0], str)  # remote
      self._TypeValidator(cmd_arg[1], str)  # local
      file_ext = os.path.splitext(cmd_arg[1])[1]
      if file_ext not in self.FILE_EXT_SUPPORTED:
        raise ValidationError('Invalid file type: %s' % cmd_arg[1])
      if len(cmd_arg) > 2:  # hash
        for arg in cmd_arg[2]:
          self._TypeValidator(arg, str)

  def _AddDriver(self, mount_dir):
    """Command used to process drivers in a given directory.

    This command will process all fo the .inf file in a folder recursively. It
    can be used regardless of how the drivers are added to the local machine.

    If the exit code for the parsed command is anything other than zero, report
    fatal error.

    Args:
      mount_dir: local directory where the driver .inf files can be found.

    Raises:
      ConfigRunnerError: Error during driver application.
    """
    dism = ['{} /Image:c: /Add-Driver /Driver:{} /Recurse'.format(
        constants.WINPE_DISM, mount_dir)]
    ex = Execute([dism], self._build_info)
    try:
      ex.Run()
    except ActionError as e:
      raise ActionError('Error applying drivers to image from %s. (%s)' %
                        (mount_dir, e))

  def _ProcessWim(self, wim_file):
    """Processes WIM driver files using DISM commands.

    Runs necessary commands to process a driver file in WIM format

    Args:
      wim_file: current file location.

    Raises:
      ConfigRunnerError: Failure mounting or unmounting WIM.
    """
    mount_dir = '%s\\Drivers\\' % constants.SYS_CACHE

    # dism commands
    mount = [
        '{} /Mount-Image /ImageFile:{} /MountDir:{} /ReadOnly /Index:1'.format(
            constants.WINPE_DISM, wim_file, mount_dir)
    ]
    unmount = ['{} /Unmount-Image /MountDir:{} /Discard'.format(
        constants.WINPE_DISM, mount_dir)]

    # create mount directory
    file_util.CreateDirectories(mount_dir)

    # mount image
    ex = Execute([mount], self._build_info)
    try:
      ex.Run()
    except ActionError as e:
      raise ActionError('Unable to mount image %s. (%s)' % (wim_file, e))

    logging.info('Applying %s image to main disk.', wim_file)
    self._AddDriver(mount_dir)

    # Unmount after running
    ex = Execute([unmount], self._build_info)
    try:
      ex.Run()
    except ActionError as e:
      raise ActionError('Error unmounting image. Unable to continue. (%s)' % e)
