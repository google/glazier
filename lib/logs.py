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

"""Set up logging for all imaging tools."""

import logging
import logging.handlers
from glazier.lib import constants


EVT_LOG_ID = 'GlazierBuildLog'


class LogError(Exception):
  pass


def GetLogsPath():
  path = constants.SYS_LOGS_PATH
  if constants.FLAGS.environment == 'WinPE':
    path = constants.WINPE_LOGS_PATH
  return path


def Setup():
  """Sets up the logging environment."""
  log_file = '%s\\%s' % (GetLogsPath(), constants.BUILD_LOG_FILE)

  logger = logging.getLogger()
  logger.setLevel(logging.DEBUG)

  # file
  try:
    fh = logging.FileHandler(log_file)
  except IOError:
    raise LogError('Failed to open log file %s.' % log_file)

  formatter = logging.Formatter(
      '%(asctime)s.%(msecs)03d\t%(filename)s:%(lineno)d] %(message)s',
      datefmt='%Y-%m-%d %H:%M:%S')
  fh.setFormatter(formatter)
  fh.setLevel(logging.DEBUG)

  # console
  ch = logging.StreamHandler()
  ch.setLevel(logging.INFO)

  if constants.FLAGS.environment != 'WinPE':
    event_handler = logging.handlers.NTEventLogHandler(EVT_LOG_ID)
    event_handler.setLevel(logging.INFO)
    logger.addHandler(event_handler)

  # add the handlers to the logger
  logger.addHandler(fh)
  logger.addHandler(ch)
