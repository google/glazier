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


class GlazierError(Exception):
  """Base error for all other Glazier errors."""

  def __init__(
      self, error_code: Optional[int] = None, message: Optional[str] = None):

    error_code = error_code if error_code is not None else 4000
    message = message if message is not None else 'Unknown Exception'

    self.error_code = error_code
    message = f'{message} (Error Code: {error_code})'

    super().__init__(message)


class UnsupportedPEError(GlazierError):
  """Error raised when an image has an outdated version of WinPE."""

  def __init__(self):
    message = """
                  !!!!! Warning !!!!!

    This image is not running the latest WinPE version.

    This scenario typically occurs when you are booting off of an outdated
    .iso file. Please update before continuing.

    """
    super().__init__(4100, message)


class UnsupportedModelError(GlazierError):

  def __init__(self, model: str):
    super().__init__(
        4101, f'System OS/model does not have imaging support: {model}')


class ExecError(GlazierError):

  def __init__(self, command: str):
    super().__init__(4141, f'Failed to execute [{command}]')


class ExecTimeoutError(GlazierError):

  def __init__(self, command: str, seconds: int):
    super().__init__(
        4142, f'Failed to execute [{command}] after [{seconds}] second(s)')


class ExecReturnError(GlazierError):

  def __init__(self, command: str, exit_code: int):
    super().__init__(
        4143, f'Executing [{command}] returned invalid exit code [{exit_code}]')


class ExecReturnOutError(GlazierError):

  def __init__(self, command: str, exit_code: int, output: str):
    message = (
        f'Executing [{command}] returned invalid exit code [{exit_code}]: '
        f'{output}')
    super().__init__(4144, message)


class ConfigBuilderError(GlazierError):

  def __init__(self):
    super().__init__(4300, 'Failed to build the task list')


class ConfigRunnerError(GlazierError):

  def __init__(self):
    super().__init__(4301, 'Failed to execute the task list')


class SysInfoError(GlazierError):

  def __init__(self):
    super().__init__(4311, 'Error gathering system information')


class UnknownActionError(GlazierError):

  def __init__(self, action: str):
    super().__init__(4312, f'Unknown imaging action [{action}]')


class UnknownPolicyError(GlazierError):

  def __init__(self, policy: str):
    super().__init__(4313, f'Unknown imaging policy [{policy}]')


class CheckUrlError(GlazierError):

  def __init__(self, url: str):
    super().__init__(4314, f'Failed to verify url [{url}]')


class RegistrySetError(GlazierError):

  def __init__(self):
    super().__init__(4340, 'Failed to set registry value')


class WebServerError(GlazierError):

  def __init__(self):
    super().__init__(5000, 'Failed to reach web server')


class ServiceError(GlazierError):

  def __init__(self):
    super().__init__(5300, 'Service unavailable')
