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
from glazier.lib import buildinfo
from glazier.lib import logs
from glazier.lib import winpe

from glazier.lib import constants
from glazier.lib import errors


def log_and_exit(build_info: buildinfo.BuildInfo,
                 exception,
                 collect: bool = True):
  """Logs a user-facing error message and exits.

  This function handles all Glazier Exceptions by sequentially:
    - (Optional) Collecting logs to a zip folder on disk
    - Logging the full traceback to the debug log
    - Constructing the user-facing failure string, consisting of:
      * The message to accompany the failure
      * The exception object, and if available, the file and line
         number of the root exception
      * The user-facing help message containing where to look for logs and
         where to go for further assistance.
    - Log the user-facing failure string
    - Exit Glazier with code 1

  Args:
    build_info: The active BuildInfo class.
    exception: The Exception object.
    collect: Whether to collect log files.
  """
  # Start by collecting logs, if specified.
  if collect:
    try:
      logs.Collect(os.path.join(build_info.CachePath(), r'\glazier_logs.zip'))
    except logs.Error as e:
      logging.error('logs collection failed with %s', e)

  # Log the full traceback to _BUILD_LOG to assist in troubleshooting
  logging.debug(traceback.format_exc())

  # Start composing the detailed failure message to present to the user.
  string = '\n\n\n********** IMAGING PROCESS FAILED **********\n\n'

  string += (
      '* Glazier encountered the following error(s) while imaging.\n'
      '  Please consult the troubleshooting links for solutions.\n\n')
  glazier_errors = errors.get_glazier_error_lineage(exception)

  # If any GlazierErrors are at fault, print out the descriptive string
  # representation of each one, along with a link to the relevant
  # troubleshooting documentation.
  if glazier_errors:
    for i, glazier_error in enumerate(glazier_errors, start=1):
      string += (f'  {i}. {glazier_error}\n'
                 f'     Troubleshooting: '
                 f'{constants.HELP_URI}#{glazier_error.error_code}\n\n')

  # Otherwise, no GlazierErrors are found, so we're dealing with something we
  # haven't seen before. Direct the user to the default error code
  # documentation.
  else:
    string += (f'  1. {exception}\n'
               f'     Troubleshooting: '
               f'{constants.HELP_URI}#{errors.ErrorCode.DEFAULT}\n\n')

  # Print out the location of the logs.
  build_log = constants.SYS_BUILD_LOG
  if winpe.check_winpe():
    build_log = constants.WINPE_BUILD_LOG
  string += f'* Logs from the imaging process can be found at: {build_log}\n\n'

  # Append a matching footer.
  string += '********************************************\n\n'

  # Print everything and bail.
  logging.critical(string, exc_info=False)
  sys.exit(1)
