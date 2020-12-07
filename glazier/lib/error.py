# Lint as: python3
# Copyright 2020 Google Inc. All Rights Reserved.
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
"""Standarize logging for all errors."""

import functools
import logging
import os
import sys
from typing import Any, Optional
import zipfile

from glazier.lib import buildinfo
from glazier.lib import constants
import glazier.lib.winpe

_SUFFIX = (f'Need help? Visit {constants.HELP_URI}')

build_info = buildinfo.BuildInfo()


def get_message(code: int, **kwargs) -> str:
  """Return dict value of a given error code.

  Args:
    code: Error code to return message for.
    **kwargs: Key/value pairs used in string.format() replacements in the error
      message.

  Returns:
    Message associated to the error code.

  Raises:
    GlazierError: Failed to determine error message from code
  """
  # TODO: Investigate how to gaurentee unique error codes
  errors: dict[int, str] = {
      1337: 'Reserved {}',
      4000: 'Uncaught exception',
      4301: 'Failed to determine error message from code',
      4302: 'Failed to collect logs',
      5000: 'Failed to reach web server',
      5300: 'Service unavailable',
  }

  error_msg = errors.get(code)

  if not error_msg:
    raise GlazierError(4301)

  # Enable passing variables to the errors dict by optionally inserting values
  # associated with the keyword arguments via string.format().
  return str(error_msg.format(*kwargs.values()))


@functools.lru_cache()
def _get_logs_path() -> str:
  if glazier.lib.winpe.check_winpe():
    return constants.WINPE_LOGS_PATH
  return constants.SYS_LOGS_PATH


@functools.lru_cache()
def _cache_path() -> str:
  if glazier.lib.winpe.check_winpe():
    return constants.WINPE_CACHE
  return constants.SYS_CACHE


def zip_logs():
  """Collect Glazier logs into a zip file.

  Raises:
    IOError,ValueError: Failed to collect logs
  """
  try:
    path = os.path.join(_cache_path(), 'glazier_logs.zip')
    arc = zipfile.ZipFile(path, mode='w')
    for root, _, files in os.walk(_get_logs_path()):
      for f in files:
        arc.write(os.path.join(root, f))
    arc.close()
  except (IOError, ValueError) as e:
    raise GlazierError(4302, e, False)


class GlazierError(Exception):
  """Custom exception class for Glazier errors."""

  def __init__(self,
               code: int = 4000,
               exception: Optional[Any] = None,
               collect: bool = True,
               **kwargs):
    """Log a terminating failure.

    Args:
      code: Error code to append to the failure message.
      exception: Exception message string.
      collect: Whether to collect log files.
      **kwargs: Key/value pairs of any number of string replacements in the
      error message.
    """
    super(GlazierError, self).__init__()

    msg = f'{get_message(code, **kwargs)}\n\n'

    # TODO: Add exception file and lineno.
    if exception:
      msg += f'Exception: {exception}\n\n'

    msg += f'{_SUFFIX}#{code}'

    if collect:
      zip_logs()

    logging.critical(msg)
    sys.exit(1)  # Necessary to avoid traceback
