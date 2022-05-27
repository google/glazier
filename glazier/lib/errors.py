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

from typing import Optional

DEFAULT_ERROR_CODE = 7000  # Was previously 4000.


class GlazierError(Exception):
  """Base error for all other Glazier errors."""

  def __init__(
      self, error_code: Optional[int] = None, message: Optional[str] = None):

    self.error_code = (
        error_code if error_code is not None else DEFAULT_ERROR_CODE)
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


class UnsupportedPEError(GlazierError):
  """Error raised when an image has an outdated version of WinPE."""

  def __init__(self):
    message = """
                  !!!!! Warning !!!!!

    This image is not running the latest WinPE version.

    This scenario typically occurs when you are booting off of an outdated
    .iso file. Please update before continuing.

    """
    super().__init__(error_code=7001, message=message)  # Was previously 4100.


class UnsupportedModelError(GlazierError):

  def __init__(self, model: str):
    super().__init__(
        error_code=7002,  # Was previously 4101.
        message=f'System OS/model does not have imaging support: {model}')


class ExecError(GlazierError):

  def __init__(self, command: str):
    super().__init__(
        error_code=7003,  # Was previously 4141.
        message=f'Failed to execute [{command}]')


class ExecTimeoutError(GlazierError):

  def __init__(self, command: str, seconds: int):
    super().__init__(
        error_code=7004,  # Was previously 4142.
        message=f'Failed to execute [{command}] after [{seconds}] second(s)')


class ExecReturnError(GlazierError):

  def __init__(self, command: str, exit_code: int):
    message = (
        f'Executing [{command}] returned invalid exit code [{exit_code}]'
    )
    super().__init__(
        error_code=7005,  # Was previously 4143.
        message=message)


class ExecReturnOutError(GlazierError):

  def __init__(self, command: str, exit_code: int, output: str):
    message = (
        f'Executing [{command}] returned invalid exit code [{exit_code}]: '
        f'{output}')
    super().__init__(
        error_code=7006,  # Was previously 4144.
        message=message)


class ConfigBuilderError(GlazierError):

  def __init__(self):
    super().__init__(
        error_code=7007,  # Was previously 4300.
        message='Failed to build the task list')


class ConfigRunnerError(GlazierError):

  def __init__(self):
    super().__init__(
        error_code=7008,  # Was previously 4301.
        message='Failed to execute the task list')


class SysInfoError(GlazierError):

  def __init__(self):
    super().__init__(
        error_code=7009,  # Was previously 4311.
        message='Error gathering system information')


class UnknownActionError(GlazierError):

  def __init__(self, action: str):
    super().__init__(
        error_code=7010,  # Was previously 4312.
        message=f'Unknown imaging action [{action}]')


class UnknownPolicyError(GlazierError):

  def __init__(self, policy: str):
    super().__init__(
        error_code=7011,  # Was previously 4313.
        message=f'Unknown imaging policy [{policy}]')


class CheckUrlError(GlazierError):

  def __init__(self, url: str):
    super().__init__(
        error_code=7012,  # Was previously 4314.
        message=f'Failed to verify url [{url}]')


class RegistrySetError(GlazierError):

  def __init__(self):
    super().__init__(
        error_code=7013,  # Was previously 4340.
        message='Failed to set registry value')


class WebServerError(GlazierError):

  def __init__(self):
    super().__init__(
        error_code=7014,  # Was previously 5000.
        message='Failed to reach web server')


class ServiceError(GlazierError):

  def __init__(self):
    super().__init__(
        error_code=7015,  # Was previously 5300.
        message='Service unavailable')


class CacheError(GlazierError):

  def __init__(self, file_path: str):
    message = f'Unable to download required file: {file_path}'
    super().__init__(error_code=7016, message=message)


class BeyondCorpError(GlazierError):
  pass


class BeyondCorpGiveUpError(BeyondCorpError):

  def __init__(self, tries: int, elapsed: float):
    message = (
        f'Failed after {tries} attempt(s) over {elapsed:0.1f} seconds.\n\n'
        'Do you have a valid network configuration?'
    )
    super().__init__(error_code=7017, message=message)


class BeyondCorpSeedFileError(BeyondCorpError):

  def __init__(self):
    super().__init__(error_code=7018, message='BeyondCorp seed file not found')


class BeyondCorpDriveLetterError(BeyondCorpError):

  def __init__(self, message: str):
    super().__init__(error_code=7019, message=message)


class BeyondCorpSignedUrlRequestError(BeyondCorpError):

  def __init__(self, message: str):
    super().__init__(error_code=7020, message=message)


class BeyondCorpSignedUrlResponseError(BeyondCorpError):

  def __init__(self, status_code: str, status: str):
    message = (
        f'Invalid response from signed url. '
        f'Status Code: {status_code}, Status: {status}'
    )
    super().__init__(error_code=7021, message=message)


class BinaryExecutionError(GlazierError):

  def __init__(self, message: str):
    super().__init__(error_code=7022, message=message)


class MissingBuildInfoFileError(GlazierError):

  def __init__(self):
    super().__init__(
        error_code=7023,
        message='Could not locate build info file.')


class UndeterminedImageIdError(GlazierError):

  def __init__(self, path: str):
    super().__init__(
        error_code=7024,
        message=f'Could not determine image ID from file: {path}')


class DownloadError(GlazierError):
  pass


class DownloadGiveUpError(DownloadError):

  def __init__(self, tries: int, elapsed: float):
    super().__init__(
        error_code=7025,
        message=f'Failed after {tries} attempt(s) over {elapsed:0.1f} seconds')


class FailedDownloadError(DownloadError):

  def __init__(self, url: str, code: int):
    super().__init__(
        error_code=7026,
        message=f'Invalid return code [{code}] for file {url}')


class InvalidRemoteUrlError(DownloadError):

  def __init__(self, url: str):
    super().__init__(
        error_code=7027,
        message=f'Invalid remote server URL "{url}".')


class LocalFileCopyError(DownloadError):

  def __init__(self, src: str, dest: str):
    super().__init__(
        error_code=7028,
        message=f'Unable to copy local file from {src} to {dest}')


class MissingFileStreamError(DownloadError):

  def __init__(self):
    super().__init__(
        error_code=7029,
        message='Cannot save to disk, missing file stream')


class StreamToDiskError(DownloadError):

  def __init__(self, message: str):
    super().__init__(error_code=7030, message=message)


class FileValidationError(DownloadError):

  def __init__(self, message: str):
    super().__init__(error_code=7031, message=message)


class FileError(GlazierError):
  pass


class FileMoveError(FileError):

  def __init__(self, src: str, dest: str):
    super().__init__(
        error_code=7032, message=f'Failed to move file from {src} to {dest}')


class FileRemoveError(FileError):

  def __init__(self, path: str):
    super().__init__(error_code=7033, message=f'Failed to remove file: {path}')


class FileWriteError(FileError):

  def __init__(self, path: str):
    super().__init__(error_code=7034, message=f'Failed to write file: {path}')


class FileReadError(FileError):

  def __init__(self, path: str):
    super().__init__(error_code=7035, message=f'Failed to read file: {path}')


class BuildInfoError(GlazierError):

  def __init__(self, message: str):
    super().__init__(error_code=7036, message=message)


class SetTitleError(GlazierError):

  def __init__(self):
    super().__init__(error_code=7037, message='Failed to set console title')


class GooGetError(GlazierError):
  pass


class GooGetFlagError(GooGetError):

  def __init__(self, message: str):
    super().__init__(error_code=7038, message=message)


class MissingGooGetBinaryError(GooGetError):

  def __init__(self, path: str):
    message = f'Cannot find path of GooGet binary: {path}'
    super().__init__(error_code=7039, message=message)


class MissingGooGetPackageError(GooGetError):

  def __init__(self):
    super().__init__(
        error_code=7040, message='Missing package name for GooGet install.')


class GooGetCommandFailureError(GooGetError):

  def __init__(self, retries: int):
    message = f'GooGet command failed after {retries} attempts'
    super().__init__(error_code=7041, message=message)


class FileCopyError(GlazierError):

  def __init__(self, src: str, dest: str):
    super().__init__(
        error_code=7042, message=f'Failed to copy file from {src} to {dest}')


class DirectoryCreationError(GlazierError):

  def __init__(self, dirname: str):
    super().__init__(
        error_code=7043, message=f'Unable to create directory: {dirname}')


class RegistryRemoveError(GlazierError):

  def __init__(self):
    super().__init__(
        error_code=7044, message='Failed to remove registry value')


class StageExpirationError(GlazierError):

  def __init__(self, stage_id: int):
    super().__init__(
        error_code=7045, message=f'Active stage {stage_id} has expired')


class StageStartError(GlazierError):

  def __init__(self, stage_id: int):
    message = f'Stage {stage_id} does not contain a valid Start time.'
    super().__init__(error_code=7046, message=message)


class InvalidStageIdError(GlazierError):

  def __init__(self, stage_id_type: type(type)):
    message = f'Invalid stage ID type; got: {stage_id_type}, want: int'
    super().__init__(error_code=7047, message=message)


class FailedDomainJoinError(GlazierError):

  def __init__(self, attempts: int):
    message = f'Failed to join domain after {attempts} attempt(s).'
    super().__init__(error_code=7048, message=message)


class ActionError(GlazierError):

  def __init__(self, message: Optional[str] = None):
    super().__init__(error_code=7049, message=message)


class ValidationError(GlazierError):

  def __init__(self, message: str):
    super().__init__(error_code=7050, message=message)


class LogCopyError(GlazierError):

  def __init__(self, message: Optional[str] = None):
    super().__init__(error_code=7051, message=message)


class ConfigError(GlazierError):

  def __init__(self, message: Optional[str] = None):
    super().__init__(error_code=7052, message=message)
