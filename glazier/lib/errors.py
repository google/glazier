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
"""Creates custom error class and centrally define all errors.

See https://google.github.io/glazier/error_codes more information.
"""

import enum

from typing import Optional


@enum.unique
class ErrorCode(enum.IntEnum):
  """Unique error codes for all anticipated Glazier errors."""

  # Default code, ideally shouldn't ever be encountered. Was previously 4000.
  DEFAULT = 7000

  # An image has an outdated version of WinPE. Was previously 4100.
  UNSUPPORTED_WINPE_VERSION = 7001

  # Imaging of the system is not supported. Was previously 4101.
  UNSUPPORTED_MODEL = 7002

  # Execution of an external command failed. Was previously 4141.
  EXECUTION_FAILED = 7003

  # Execution of an external command timed out. Was previously 4142.
  EXECUTION_TIMEOUT = 7004

  # An external command returned an invalid exit code. Was previously 4143.
  EXECUTION_RETURN = 7005

  # Held to prevent reuse. Was previously EXECUTION_RETURN_OUT (4144).
  DEPRECATED_05 = 7006

  # A Glazier task list cannot be built. Was previously 4300.
  FAILED_TASK_LIST_BUILD = 7007

  # A Glazier task list cannot be executed. Was previously 4301.
  FAILED_TASK_LIST_RUN = 7008

  # Error while gathering system information. Was previously 4311.
  SYS_INFO = 7009

  # An unknown Glazier action is encountered. Was previously 4312.
  UNKNOWN_ACTION = 7010

  # An unknown Glazier policy is encountered. Was previously 4313.
  UNKNOWN_POLICY = 7011

  # A request to a URL returned an unexpected HTTP code. Was previously 4314.
  FAILED_URL_VERIFICATION = 7012

  # Error while writing to the registry. Was previously 4340.
  REGISTRY_WRITE_ERROR = 7013

  # Held to prevent reuse. Was previously UNREACHABLE_WEB_SERVER (5000).
  DEPRECATED_01 = 7014

  # Held to prevent reuse. Was previously SERVICE_ERROR (5300).
  DEPRECATED_02 = 7015

  # A file cannot be found in cache.
  CACHE_MISS = 7016

  # Failure after too many BeyondCorp errors.
  BEYONDCORP_GIVE_UP = 7017

  # No BeyondCorp seed file found.
  BEYONDCORP_SEED_FILE_MISSING = 7018

  # Failed to determine BeyondCorp drive letter.
  BEYONDCORP_DRIVE_LETTER_ERROR = 7019

  # Error while making BeyondCorp request.
  BEYONDCORP_REQUEST_ERROR = 7020

  # Error when receiving BeyondCorp response.
  BEYONDCORP_RESPONSE_ERROR = 7021

  # Held to prevent reuse. Was previously TASK_LIST_REMOVE_ERROR (4303).
  DEPRECATED_06 = 7022

  # Held to prevent reuse. Was previously TASK_LIST_BUILD_ERROR (4302).
  DEPRECATED_07 = 7023

  # Held to prevent reuse. Was previously TASK_LIST_EXECUTE_ERROR (4304).
  DEPRECATED_08 = 7024

  # System is not compatible with an imaging policy.
  POLICY_VERIFICATION_ERROR = 7025

  # Failed to move a file.
  FILE_MOVE_ERROR = 7026

  # Failed to remove a file.
  FILE_REMOVE_ERROR = 7027

  # Failed to write to a file.
  FILE_WRITE_ERROR = 7028

  # Failed to read from a file.
  FILE_READ_ERROR = 7029

  # Failed to download a file.
  FILE_DOWNLOAD_ERROR = 7030

  # An imaging stage has taken too long.
  STAGE_EXPIRATION_ERROR = 7031

  # Cannot determine the starting time of the current stage.
  STAGE_INVALID_START_TIME_ERROR = 7032

  # Invalid stage ID encountered.
  STAGE_INVALID_ID_ERROR = 7033

  # Error encountered while exiting a stage.
  STAGE_EXIT_ERROR = 7034

  # Held to prevent reuse. Was previously STAGE_INVALID_TYPE_ERROR.
  DEPRECATED_03 = 7035

  # Error encountered while updating a stage.
  STAGE_UPDATE_ERROR = 7036

  # Error while loading timezone data.
  TIMEZONE_ERROR = 7037

  # KeyError while parsing build_info.yaml.
  BUILD_INFO_KEY_MISSING = 7038

  # Unable to locate build_info.yaml.
  BUILD_INFO_FILE_MISSING = 7039

  # Unknown glazier_spec flag.
  UNKNOWN_SPEC = 7040

  # Error importing a Python module.
  MODULE_NOT_AVAILABLE = 7041

  # Various errors with GooGet flags.
  GOOGET_FLAG_ERROR = 7042

  # Invalid path to the GooGet binary.
  GOOGET_BINARY_NOT_FOUND = 7043

  # GooGet package name not provided.
  GOOGET_MISSING_PACKAGE_NAME = 7044

  # GooGet command failed for some reason.
  GOOGET_COMMAND_FAILED = 7045

  # Held to prevent reuse. Was previously AUTOBUILD_ERROR.
  DEPRECATED_04 = 7046

  # Failed to enable TPM via PowerShell.
  BITLOCKER_ENABLE_TPM_FAILED = 7047

  # Failed to activate BitLocker.
  BITLOCKER_ACTIVATION_FAILED = 7048

  # Unknown BitLocker mode.
  BITLOCKER_UNKNOWN_MODE = 7049

  # Various errors while copying log files.
  LOG_COPY_FAILURE = 7050

  # Error while trying to set the console title.
  CANNOT_SET_CONSOLE_TITLE = 7051

  # Download failed after a number of retries.
  DOWNLOAD_GIVE_UP = 7052

  # Download failed with an unexpected error code.
  DOWNLOAD_FAILED = 7053

  # Download URL is invalid.
  DOWNLOAD_INVALID_REMOTE_URL = 7054

  # Local file copy failure.
  DOWNLOAD_LOCAL_COPY_ERROR = 7055

  # Failure to obtain a signed URL.
  DOWNLOAD_SIGNED_URL_ERROR = 7056

  # Error while streaming download to disk.
  DOWNLOAD_MISSING_FILE_STREAM = 7057

  # Error while streaming download to disk.
  DOWNLOAD_STREAM_TO_DISK_ERROR = 7058

  # Unable to validate downloaded file.
  DOWNLOAD_VALIDATION_ERROR = 7059

  # No response from NTP server.
  NO_NTP_RESPONSE = 7060

  # Unable to determine identity of system.
  SPLICE_IDENTITY_ERROR = 7061

  # Failed to join domain. Was previously 4304.
  DOMAIN_JOIN_FAILURE = 7062

  # PowerShell parameter not supported.
  POWERSHELL_UNSUPPORTED_PARAMETER = 7063

  # Error encountered during PowerShell execution.
  POWERSHELL_EXECUTION_ERROR = 7064

  # Invalid path provided to PowerShell.
  POWERSHELL_INVALID_PATH = 7065

  # An unsupported execution policy was provided.
  POWERSHELL_UNSUPPORTED_EXECUTION_POLICY = 7066

  # Error encountered while collecting logs.
  LOGS_COLLECTION_ERROR = 7067

  # Unable to open a log file.
  LOGS_OPEN_ERROR = 7068

  # A particular file wasn't found.
  FILE_NOT_FOUND = 7069

  # Illegal .yaml pin encountered.
  ILLEGAL_PIN = 7070

  # Error encountered while reading a .yaml file.
  YAML_FILE_ERROR = 7071

  # Error while reading from WMI.
  WMI_ERROR = 7072

  # Unknown OS code encountered.
  UNKNOWN_OS_CODE = 7073

  # Unable to determine the host OS.
  UNDETERMINED_HOST_OS = 7074

  # Unable to find a corresponding release.
  UNSUPPORTED_RELEASE_VERSION = 7075

  # Failed to copy a file.
  FILE_COPY_ERROR = 7076

  # Failed to create a directory.
  DIRECTORY_CREATION_ERROR = 7077

  # Failed to delete from the registry.
  REGISTRY_DELETE_ERROR = 7078

  # Failed to write to the registry.
  IDENTITY_WRITE_ERROR = 7079

  # Error while executing a Glazier action.
  ACTION_ERROR = 7080

  # Error while validating a Glazier command.
  VALIDATION_ERROR = 7081

  # Error while processing a config file.
  CONFIG_ERROR = 7082

  # Error while setting an imaging timer.
  SET_TIMER_ERROR = 7083


class GlazierError(Exception):
  """Base error for all other Glazier errors."""

  def __init__(
      self,
      error_code: Optional[int] = ErrorCode.DEFAULT,
      message: Optional[str] = None):

    self.error_code = (
        error_code if error_code is not None else ErrorCode.DEFAULT)
    self.message = message if message is not None else 'Unknown Exception'

    super().__init__()

  def __str__(self):
    return f'{self.message} (Error Code: {self.error_code})'


def get_glazier_error_lineage(ex):
  """Extracts all GlazierErrors in the lineage of the given Exception.

  Args:
    ex: The Exception whose GlazierError lineage we want.

  Returns:
    The lineage of GlazierErrors which led to the argument Exception, in order
    of earliest-raised to latest-raised.

  Raises:
    ValueError: if no Exception is provided.
  """
  if ex is None:
    raise ValueError('Exception argument cannot be None')

  glazier_errors = []
  current_ex = ex

  while current_ex is not None:
    if isinstance(current_ex, GlazierError):
      glazier_errors.insert(0, current_ex)
    current_ex = current_ex.__cause__

  return glazier_errors
