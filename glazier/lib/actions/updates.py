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

"""Actions for managing updates for specific machines."""

import logging
import os
from glazier.lib import execute
from glazier.lib import file_util
from glazier.lib.actions.base import ActionError
from glazier.lib.actions.base import BaseAction
from glazier.lib.actions.base import ValidationError
from glazier.lib.actions.files import Get

from glazier.lib import constants


class UpdateMSU(BaseAction):
  """Downloads file and verifies extension.

  File is downloaded and processed based on supported file extension.
  file can then be processed to be used by dism commands.

  Method can be expanded to access and process other formats allowed by DISM.
  Also can be used to process multiple files.

  Raises:
    ActionError: Call with unsupported file type.
  """
  FILE_EXT_SUPPORTED = ['.msu']

  def Run(self):
    for msu in self._args:
      dst = str(msu[1])
      file_ext = os.path.splitext(dst)[1]

      if file_ext not in self.FILE_EXT_SUPPORTED:
        raise ActionError(f'Unsupported update file format {dst}.')

      g = Get([msu], self._build_info)
      g.Run()

      logging.info('Found MSU file, processing update using DISM.')
      self._ProcessMsu(dst)

  def Validate(self):
    self._TypeValidator(self._args, list)
    for cmd_arg in self._args:
      self._TypeValidator(cmd_arg, list)
      if not 2 <= len(cmd_arg) <= 3:
        raise ValidationError(f'Invalid args length: {len(cmd_arg)}')
      self._TypeValidator(cmd_arg[0], str)  # remote
      self._TypeValidator(cmd_arg[1], str)  # local
      file_ext = os.path.splitext(cmd_arg[1])[1]
      if file_ext not in self.FILE_EXT_SUPPORTED:
        raise ValidationError(f'Invalid file type: {cmd_arg[1]}')
      if len(cmd_arg) > 2:  # hash
        for arg in cmd_arg[2]:
          self._TypeValidator(arg, str)

  def _ProcessMsu(self, msu_file):
    """Command used to process updates downloaded.

    This command will apply updates to an image.

    If the exit code for the parsed command is anything other than zero, report
    fatal error.

    Args:
      msu_file: current file location.

    Raises:
      ActionError: Error during update application.
    """

    scratch_dir = '%s\\Updates\\' % constants.SYS_CACHE

    # create scratch directory
    file_util.CreateDirectories(scratch_dir)

    logging.info('Applying %s image to main disk.', msu_file)

    # Apply updates to  image
    try:
      execute.execute_binary(
          constants.WINPE_DISM, [
              '/image:c:\\', '/Add-Package', f'/PackagePath:{msu_file}',
              f'/ScratchDir:{scratch_dir}'
          ],
          shell=True)
    except execute.Error as e:
      raise ActionError(f'Failed to process update {msu_file}') from e
