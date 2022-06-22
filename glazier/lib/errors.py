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

  DEFAULT = 7000  # Was previously 4000.
  UNSUPPORTED_WINPE_VERSION = 7001  # Was previously 4100.
  UNSUPPORTED_MODEL = 7002  # Was previously 4101.
  EXECUTION_FAILED = 7003  # Was previously 4141.
  EXECUTION_TIMEOUT = 7004  # Was previously 4142.
  EXECUTION_RETURN = 7005  # Was previously 4143.
  EXECUTION_RETURN_OUT = 7006  # Was previously 4144.
  FAILED_TASK_LIST_BUILD = 7007  # Was previously 4300.
  FAILED_TASK_LIST_RUN = 7008  # Was previously 4301.
  SYS_INFO = 7009  # Was previously 4311.
  UNKNOWN_ACTION = 7010  # Was previously 4312.
  UNKNOWN_POLICY = 7011  # Was previously 4313.
  FAILED_URL_VERIFICATION = 7012  # Was previously 4314.
  FAILED_REGISTRY_WRITE = 7013  # Was previously 4340.
  UNREACHABLE_WEB_SERVER = 7014  # Was previously 5000.
  SERVICE_ERROR = 7015  # Was previously 5300.
  CACHE_MISS = 7016
  BEYONDCORP_GIVE_UP = 7017
  BEYONDCORP_SEED_FILE_MISSING = 7018
  BEYONDCORP_DRIVE_LETTER_ERROR = 7019
  BEYONDCORP_REQUEST_ERROR = 7020
  BEYONDCORP_RESPONSE_ERROR = 7021
  TASK_LIST_REMOVE_ERROR = 7022  # Was previously 4303.
  TASK_LIST_BUILD_ERROR = 7023  # Was previously 4302.
  TASK_LIST_EXECUTE_ERROR = 7024  # Was previously 4304.
  POLICY_VERIFICATION_ERROR = 7025
  FILE_MOVE_ERROR = 7026
  FILE_REMOVE_ERROR = 7027
  FILE_WRITE_ERROR = 7028
  FILE_READ_ERROR = 7029
  FILE_DOWNLOAD_ERROR = 7030
  STAGE_EXPIRATION_ERROR = 7031
  STAGE_INVALID_START_TIME_ERROR = 7032
  STAGE_INVALID_ID_ERROR = 7033
  STAGE_EXIT_ERROR = 7034
  STAGE_INVALID_TYPE_ERROR = 7035
  STAGE_UPDATE_ERROR = 7036
  TIMEZONE_ERROR = 7037
  BUILD_INFO_KEY_MISSING = 7038
  BUILD_INFO_FILE_MISSING = 7039
  UNKNOWN_SPEC = 7040
  MODULE_NOT_AVAILABLE = 7041
  GOOGET_FLAG_ERROR = 7042
  GOOGET_BINARY_NOT_FOUND = 7043
  GOOGET_MISSING_PACKAGE_NAME = 7044
  GOOGET_COMMAND_FAILED = 7045
  AUTOBUILD_ERROR = 7046
  BITLOCKER_ENABLE_TPM_FAILED = 7047
  BITLOCKER_ACTIVATION_FAILED = 7048
  BITLOCKER_UNKNOWN_MODE = 7049
  LOG_COPY_FAILURE = 7050
  CANNOT_SET_CONSOLE_TITLE = 7051
  DOWNLOAD_GIVE_UP = 7052
  DOWNLOAD_FAILED = 7053
  DOWNLOAD_INVALID_REMOTE_URL = 7054
  DOWNLOAD_LOCAL_COPY_ERROR = 7055
  DOWNLOAD_SIGNED_URL_ERROR = 7056
  DOWNLOAD_MISSING_FILE_STREAM = 7057
  DOWNLOAD_STREAM_TO_DISK_ERROR = 7058
  DOWNLOAD_VALIDATION_ERROR = 7059
  NO_NTP_RESPONSE = 7060
  SPLICE_IDENTITY_ERROR = 7061
  DOMAIN_JOIN_FAILURE = 7062


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

    s = f'{self.message} (Error Code: {self.error_code})'

    # If this exception was raised from another root-cause exception, include
    # the root-cause description in the description of this one.
    if self.__cause__ is not None:
      cause_message = (
          self.__cause__.message if isinstance(self.__cause__, GlazierError)
          else str(self.__cause__))
      s = f'{s} (Cause: {cause_message})'

    return s


class UnknownPolicyError(GlazierError):

  def __init__(self, policy: str):
    super().__init__(
        error_code=ErrorCode.UNKNOWN_POLICY,
        message=f'Unknown imaging policy [{policy}]')


class CheckUrlError(GlazierError):

  def __init__(self, url: str):
    super().__init__(
        error_code=ErrorCode.FAILED_URL_VERIFICATION,
        message=f'Failed to verify url [{url}]')


class RegistrySetError(GlazierError):

  def __init__(self):
    super().__init__(
        error_code=ErrorCode.FAILED_REGISTRY_WRITE,
        message='Failed to set registry value')


class WebServerError(GlazierError):

  def __init__(self):
    super().__init__(
        error_code=ErrorCode.UNREACHABLE_WEB_SERVER,
        message='Failed to reach web server')


class ServiceError(GlazierError):

  def __init__(self):
    super().__init__(
        error_code=ErrorCode.SERVICE_ERROR,
        message='Service unavailable')


class CacheError(GlazierError):

  def __init__(self, file_path: str):
    super().__init__(
        error_code=ErrorCode.CACHE_MISS,
        message=f'Unable to download required file: {file_path}')
