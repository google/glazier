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


_HEADER = '\n\n\n********** IMAGING PROCESS FAILED **********\n\n'
_FOOTER = '********************************************\n\n'


def _failure_message(exception) -> str:
  """Builds the user-facing failure message for an exception.

  If composing the detailed message raises, falls back to a minimal message so
  that the caller can still log it, collect logs, and exit.

  Args:
    exception: The Exception object.

  Returns:
    The failure message, including a header and footer.
  """
  try:
    body = (
        '* Glazier encountered the following error(s) while imaging.\n'
        '  Please consult the troubleshooting links for solutions.\n\n')
    glazier_errors = errors.get_glazier_error_lineage(exception)

    # If any GlazierErrors are at fault, print out the descriptive string
    # representation of each one, along with a link to the relevant
    # troubleshooting documentation.
    if glazier_errors:
      for i, glazier_error in enumerate(glazier_errors, start=1):
        body += (f'  {i}. {glazier_error}\n'
                 f'     Troubleshooting: '
                 f'{constants.HELP_URI}#{glazier_error.error_code}\n\n')

    # Otherwise, no GlazierErrors are found, so we're dealing with something we
    # haven't seen before. Direct the user to the default error code
    # documentation.
    else:
      # pyrefly: ignore[missing-attribute]
      body += (f'  1. {exception}\n'
               f'     Troubleshooting: '
               f'{constants.HELP_URI}#{errors.ErrorCode.DEFAULT}\n\n')

    # Print out the location of the logs.
    build_log = constants.SYS_BUILD_LOG
    if winpe.check_winpe():
      build_log = constants.WINPE_BUILD_LOG
    body += f'* Logs from the imaging process can be found at: {build_log}\n\n'
  except Exception:  # pylint: disable=broad-exception-caught
    logging.exception('Failed to compose the detailed failure message.')
    body = f'  1. {_exception_summary(exception)}\n\n'

  return _HEADER + body + _FOOTER


def _exception_summary(exception) -> str:
  """Describes an exception without raising.

  The exception's own string conversion may be what made composing the detailed
  message fail, so fall back to its type name and then to a constant string.

  Args:
    exception: The Exception object.

  Returns:
    A short description of the exception.
  """
  try:
    return f'{type(exception).__name__}: {exception}'
  except Exception:  # pylint: disable=broad-exception-caught
    pass
  try:
    return str(type(exception).__name__)
  except Exception:  # pylint: disable=broad-exception-caught
    return 'Unknown error'


def log_and_exit(build_info: buildinfo.BuildInfo,
                 exception,
                 collect: bool = True):
  """Logs a user-facing error message and exits.

  This function handles all Glazier Exceptions by sequentially:
    - Logging the full traceback of the exception to the debug log
    - Constructing the user-facing failure string, consisting of:
      * The message to accompany the failure
      * The exception object, and if available, the file and line
         number of the root exception
      * The user-facing help message containing where to look for logs and
         where to go for further assistance.
      If constructing the string fails, a minimal string is used instead.
    - Log the user-facing failure string
    - (Optional) Collecting logs to a zip folder on disk
    - Exit Glazier with code 1, even if any earlier step fails or is
      interrupted

  The traceback and failure string are logged before log collection, so they
  are preserved and included in the collected logs even if collection fails or
  is interrupted.

  Args:
    build_info: The active BuildInfo class.
    exception: The Exception object.
    collect: Whether to collect log files.
  """
  try:
    # Log the full traceback to _BUILD_LOG to assist in troubleshooting. Format
    # it from the passed exception, since this may be called outside of an
    # except block.
    logging.debug(
        ''.join(
            traceback.format_exception(
                type(exception), exception, exception.__traceback__
            )
        )
    )

    # Print everything before collecting logs, so it can't be lost.
    logging.critical(_failure_message(exception), exc_info=False)

    if collect:
      logs.Collect(os.path.join(build_info.CachePath(), r'\glazier_logs.zip'))
  except logs.Error as e:
    logging.error('logs collection failed with %s', e)
  except KeyboardInterrupt:
    logging.error('Interrupted before exit; logs may not have been collected.')
  except Exception:  # pylint: disable=broad-exception-caught
    logging.exception('Failed to log the failure or collect logs.')
  finally:
    # Bail with exit code 1 no matter what.
    sys.exit(1)
