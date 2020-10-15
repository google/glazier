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
import os
from typing import Text
import zipfile

from glazier.lib import buildinfo
from glazier.lib import constants
from glazier.lib import file_util
from glazier.lib import winpe


DATE_FMT = '%m%d %H:%M:%S'


class LogError(Exception):
  pass


def GetLogsPath():
  path = constants.SYS_LOGS_PATH
  if winpe.check_winpe():
    path = constants.WINPE_LOGS_PATH
  return path


def Collect(path: Text):
  """Collect Glazier logs into a zip file.

  Args:
    path: An output path for the zip file.
  """
  try:
    arc = zipfile.ZipFile(path, mode='w')
    for root, _, files in os.walk(GetLogsPath()):
      for f in files:
        arc.write(os.path.join(root, f))
    arc.close()
  except (IOError, ValueError) as e:
    raise LogError(str(e))


def Setup():
  """Sets up the logging environment."""
  build_info = buildinfo.BuildInfo()
  log_file = r'%s\%s' % (GetLogsPath(), constants.BUILD_LOG_FILE)
  file_util.CreateDirectories(log_file)

  debug_fmt = ('%(levelname).1s%(asctime)s.%(msecs)03d %(process)d {} '
               '%(filename)s:%(lineno)d]  %(message)s').format(
                   build_info.ImageID())
  info_fmt = '%(levelname).1s%(asctime)s %(filename)s:%(lineno)d] %(message)s'

  debug_formatter = logging.Formatter(debug_fmt, datefmt=DATE_FMT)
  info_formatter = logging.Formatter(info_fmt, datefmt=DATE_FMT)

  # Set default logger
  logger = logging.getLogger()
  logger.setLevel(logging.DEBUG)
  # Create empty list of handlers to enable multiple streams.
  logger.handlers = []

  # Create console handler and set level
  ch = logging.StreamHandler()
  ch.setLevel(logging.INFO)
  ch.setFormatter(info_formatter)
  logger.addHandler(ch)

  # Create file handler and set level
  try:
    fh = logging.FileHandler(log_file)
  except IOError:
    raise LogError('Failed to open log file %s.' % log_file)
  fh.setLevel(logging.DEBUG)
  fh.setFormatter(debug_formatter)
  logger.addHandler(fh)

  # Create Event Log handler and set level
  if not winpe.check_winpe():
    eh = logging.handlers.NTEventLogHandler('GlazierBuildLog')
    eh.setLevel(logging.DEBUG)
    eh.setFormatter(debug_formatter)
    logger.addHandler(eh)
