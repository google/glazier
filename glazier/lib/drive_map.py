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

"""Map network shares to drives on the local machine."""

import logging
import time

from glazier.lib import errors


class Error(errors.GlazierError):
  pass


class ModuleImportError(Error):
  """Error loading required python modules."""

  def __init__(self, module: str):
    super().__init__(
        error_code=errors.ErrorCode.MODULE_NOT_AVAILABLE,
        message=f'No module named "{module}" available on this platform')


class DriveMap(object):
  """Map and Unmap network shares."""

  def __init__(self):
    self._ModuleInit()

  def MapDrive(self, drive_letter, server_path, username=None, password=None):
    """Maps a Samba or WebDAV path to a drive letter in Windows.

    Args:
      drive_letter: The drive letter to map the Samba path to.
      server_path: The path to map to.
      username: The username to use in mapping the drive.
      password: The password to use in mapping the drive.

    Returns:
      False if drive map fails, True if drive map succeeds.
    """
    wait = 1
    limit = 65
    while wait < limit:
      try:
        self._win32wnet.WNetAddConnection2(self._win32netcon.RESOURCETYPE_DISK,
                                           drive_letter, server_path, None,
                                           username, password, 0)
        break
      except self._win32wnet.error:
        logging.error('Failed to map path %s to network drive %s.', server_path,
                      drive_letter)
        logging.error('Waiting for %s seconds.', str(wait))
        time.sleep(wait)
        wait *= 2

    if wait > limit:
      logging.error('Unable to map path, aborting.')
      return False
    return True

  def UnmapDrive(self, drive):
    """function to verify network drive connection.

    Checks if drive is connected.  Writes to temporary log if not connected.

    Args:
      drive: mapped network drive.

    Returns:
      False if no network drive connected. Returns True if drive unmaps.
    """
    try:
      self._win32wnet.WNetCancelConnection2(drive, 1, True)
    except self._win32wnet.error:
      logging.error('The network drive does not exist.')
      return False
    return True

  def _ModuleInit(self):
    """Initialize win32 platform modules.

    Raises:
      ModuleImportError: failure to import a required module
    """
    try:
      import win32wnet  # pylint: disable=g-import-not-at-top
      self._win32wnet = win32wnet
    except ImportError as e:
      raise ModuleImportError('win32wnet') from e

    try:
      import win32netcon  # pylint: disable=g-import-not-at-top
      self._win32netcon = win32netcon
    except ImportError as e:
      raise ModuleImportError('win32netcon') from e
