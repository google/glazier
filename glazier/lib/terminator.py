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


def _get_causal_chain(ex):
  """Extracts the __cause__ lineage of the given Exception.

  Args:
    ex: The Exception whose __cause__ lineage we want.

  Returns:
    The lineage of Exceptions which led to the argument Exception, in order of
    earliest-raised to latest-raised.

  Raises:
    ValueError: if no Exception is provided.
  """
  if ex is None:
    raise ValueError('Exception argument cannot be None')

  chain = [ex]
  while chain[0].__cause__ is not None:
    chain.insert(0, chain[0].__cause__)

  return chain


def _get_root_cause_exception(chain):
  """Finds the earliest-raised GlazierError in the Exception chain.

  If no GlazierError is found, defaults to the earliest Exception.

  Args:
    chain: List of Exceptions extracted from __cause__ relationships.

  Returns:
    The earliest GlazierError in the chain, or the earliest Exception if no
    GlazierError is found.

  Raises:
    ValueError: if no list is provided.
  """
  if not chain:
    raise ValueError('List argument cannot be empty or None')

  # Filter all non-GlazierErrors.
  glazier_errors = [e for e in chain if isinstance(e, errors.GlazierError)]

  # Return the earliest GlazierError in the chain, if one exists. Otherwise,
  # return the first Exception.
  return glazier_errors[0] if glazier_errors else chain[0]


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
  string = '\n\n\n***** IMAGING PROCESS FAILED *****\n\n'

  # Identify the root cause GlazierError (or Exception).
  chain = _get_causal_chain(exception)
  root_cause_exception = _get_root_cause_exception(chain)
  string += f'* Root Cause: {root_cause_exception}\n\n'

  # Print the filename and line number of the root cause if possible.
  tb = root_cause_exception.__traceback__
  if tb:
    summary = traceback.extract_tb(tb)[-1]
    location_file = os.path.split(summary.filename)[1]
    location_line = summary.lineno
    string += f'* Location: {location_file}:{location_line}\n\n'

  # Print out the location of the logs.
  build_log = constants.SYS_BUILD_LOG
  if winpe.check_winpe():
    build_log = constants.WINPE_BUILD_LOG
  string += f'* Logs: {build_log}\n\n'

  # If an originating GlazierError was identified, use the error code to point
  # the user to the troubleshooting docs. Otherwise, point to the "default"
  # troubleshooting docs.
  string += f'* Troubleshooting: {constants.HELP_URI}#'
  if isinstance(root_cause_exception, errors.GlazierError):
    string += f'{root_cause_exception.error_code}\n\n'
  else:
    string += f'{errors.ErrorCode.DEFAULT}\n\n'

  # Print everything and bail.
  logging.critical(string, exc_info=False)
  sys.exit(1)
