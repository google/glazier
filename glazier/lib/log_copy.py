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
"""This copies the build log around places."""

import logging
import logging.handlers
import shutil

# do not remove: internal placeholder 1
from glazier.lib import drive_map
from glazier.lib import gtime
from glazier.lib import logs
from glazier.lib import registry

from glazier.lib import constants
from glazier.lib import errors


class Error(errors.GlazierError):
  pass


class LogCopyError(Error):

  def __init__(self, message: str):
    super().__init__(
        error_code=errors.ErrorCode.LOG_COPY_FAILURE,
        message=message)


class LogCopyCredentials(object):
  """Supplies credentials for the log copy destination share."""

  def __init__(self):
    self._username = None
    self._password = None

  def GetUsername(self) -> str:
    """Override to provide share credentials."""
    return self._username

  def GetPassword(self) -> str:
    """Override to provide share credentials."""
    return self._password


class LogCopy(object):
  """Copies text log files around."""

  def __init__(self):
    self._logging = logging.Logger('log_copy')
    path = '%s\\log_copy.log' % logs.GetLogsPath()
    self._logging.addHandler(logging.FileHandler(path))

  def _EventLogUpload(self, source_log: str):
    """Upload the log file contents to the local EventLog."""
    event_handler = logging.handlers.NTEventLogHandler('GlazierBuildLog')
    logger = logging.Logger('eventlogger')
    logger.addHandler(event_handler)
    logger.setLevel(logging.DEBUG)

    try:
      with open(source_log, 'r') as f:
        content = f.readlines()
        for line in content:
          logger.info(line)
    except IOError as e:
      raise LogCopyError(
          'Unable to open log file. It will not be imported into '
          'the Windows Event Log.') from e

  def _GetLogFileName(self):
    """Creates the destination file name for a text log file.

    Returns:
      The full text file log name (string).
    """
    try:
      hostname = registry.get_value('name', path=constants.REG_ROOT)
    except registry.Error as e:
      raise LogCopyError(
          'Hostname could not be determined for log copy') from e

    destination_file_date = gtime.now().replace(microsecond=0)
    destination_file_date = destination_file_date.isoformat()
    destination_file_date = destination_file_date.replace(':', '')
    return 'l:\\' + hostname + '-' + destination_file_date + '.log'

  def _ShareUpload(self, source_log: str, share: str):
    """Copy the log file to a network file share.

    Args:
      source_log: Path to the source log file to be copied.
      share: The destination share to copy the file to.

    Raises:
      LogCopyError: Failure to mount share and copy log.
    """
    creds = LogCopyCredentials()
    username = creds.GetUsername()
    password = creds.GetPassword()

    mapper = drive_map.DriveMap()
    result = mapper.MapDrive('l:', share, username, password)
    if result:
      destination = self._GetLogFileName()
      try:
        shutil.copy(source_log, destination)
      except shutil.Error as e:
        raise LogCopyError('Log copy failed.') from e
      mapper.UnmapDrive('l:')
    else:
      raise LogCopyError('Drive mapping failed.')

  def EventLogCopy(self, source_log: str):
    """Copy a log file to EventLog."""
    self._EventLogUpload(source_log)

  def ShareCopy(self, source_log: str, share: str):
    """Copy a log file via CIFS."""
    self._ShareUpload(source_log, share)
