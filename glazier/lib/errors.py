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
"""Creates custom error class and centrally define all errors.

See https://google.github.io/glazier/error_codes more information.
"""

from typing import Dict, List, Optional, Type, Union

# Format: 'G<NameofError>': [Code, 'Message with optional replacements']
_ERRORS: Dict[str, List[Union[int, str]]] = {
    'GReservedError': [1337, 'Reserved {} {} {}'],
    'GUncaughtError': [4000, 'Uncaught exception'],
    'GUnsupportedPEError': [
        4100, """
                  !!!!! Warning !!!!!

    This image is not running the latest WinPE version.

    This scenario typically occurs when you are booting off of an outdated
    .iso file. Please update before continuing.

    """
    ],
    'GUnsupportedModelError': [
        4101, 'System OS/model does not have imaging support {}'
    ],
    'GExecError': [4141, 'Failed to execute [{}]'],
    'GExecTimeOutError': [4142, 'Failed to execute [{}] after [{}] second(s)'],
    'GExecReturnError': [
        4143, 'Executing [{}] returned invalid exit code [{}]'
    ],
    'GExecReturnOutError': [
        4144, 'Executing [{}] returned invalid exit code [{}]: {}'
    ],
    'GConfigBuilderError': [4300, 'Failed to build the task list'],
    'GConfigRunnerError': [4301, 'Failed to execute the task list'],
    'GSysInfoError': [4311, 'Error gathering system information'],
    'GUnknownActionError': [4312, 'Unknown imaging action [{}]'],
    'GUnknownPolicyError': [4313, 'Unknown imaging policy [{}]'],
    'GCheckUrlError': [4314, 'Failed to verify url [{}]'],
    'GRegSetError': [4340, 'Failed to set registry value'],
    'GWebServerError': [5000, 'Failed to reach web server'],
    'GServiceError': [5300, 'Service unavailable'],
}

# Required for Pytype to work with dynamic error objects
_HAS_DYNAMIC_ATTRIBUTES = True


class GlazierError(Exception):
  """Creates an error object.

  This error object can be interacted with via it's attributes directly. For
  example, the following code can be used to determine the attributes of this
  class:

  try:
    raise GlazierError('SomeException', [
                       'SomeReplacement', 'SomeOtherReplacement'])
  except GlazierError as e:
    for att in dir(e):
        print(att, getattr(e, att))

  The default code if all fails is 4000. This acts as a fallback for when there
  is an unknown exception.

  Attributes:
    code: Error code with an associated message
    message: Error message string with an associated code
    exception: Exception message string
    replacements: Any number of values that the error message should contain
  """

  def __init__(self,
               exception: Optional[Exception] = None,
               replacements: Optional[List[Union[bool, int, str]]] = None):
    self.code = 4000
    self.message = 'Unknown Exception'
    self.exception = exception

    if isinstance(exception, GlazierError):
      self.code = exception.code
      self.message = exception.message
      self.exception = exception.exception

    self.replacements = replacements
    super().__init__(exception, replacements)

  def __str__(self) -> str:
    string = ''

    if self.message:
      string = f'{self.message} '

    string += f'({self.code})'

    if self.exception:
      string += f': {self.exception}'

    return string


def _new_err(code: int, message: str) -> Type[GlazierError]:
  """Captures code and message pairs for every error.

  This method acts to store the error codes and the associated messages to be
  passed to the GlazierException class.

  Args:
    code: Error code with an associated message
    message: Error message string with an associated code

  Returns:
    GlazierError exception with all required attributes.
  """

  class Error(GlazierError):
    """Stores error information used in GlazierError."""

    def __init__(self,
                 exception: Optional[Exception] = None,
                 replacements: Optional[List[Union[bool, int, str]]] = None):
      super().__init__(exception, replacements)
      self.code: int = code
      if message and replacements:
        # Asterisk is used to unpack the values of the list
        self.message: str = f'{message.format(*replacements)}'
      elif message:
        self.message: str = message

  return Error


for key, value in _ERRORS.items():
  vars()[key] = _new_err(value[0], value[1])
