# Lint as: python3
# Copyright 2021 Google Inc. All Rights Reserved.
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
"""Terminates currently running Glazier processes."""

import logging
import os
import sys
import traceback
from typing import Optional
from glazier.lib import actions
from glazier.lib import buildinfo
from glazier.lib import constants
from glazier.lib import logs
from glazier.lib import winpe


def log_and_exit(msg: str,
                 build_info: buildinfo.BuildInfo,
                 code: int = 4000,
                 exception: Optional[Exception] = None,
                 collect: bool = True):
  """Logs a user-facing error message and exits.

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

  logging.critical(string)
  sys.exit(1)
