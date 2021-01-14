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
"""Create custom error class and centrally define all errors."""

from typing import List, Optional, Type, Union


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
               exception: Optional[str] = '',
               replacements: Optional[List[Union[bool, int, str]]] = None):
    self.code = 4000
    self.message = ''
    self.exception = exception
    self.replacements = replacements
    super().__init__(exception, replacements)

  def __str__(self) -> str:
    string = ''

    if self.message:
      string = f'{self.message} '

    string += f'({self.code})'

    # TODO: Add exception file and lineno.
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
                 exception: Optional[str] = '',
                 replacements: Optional[List[Union[bool, int, str]]] = None):
      super().__init__(exception, replacements)
      self.code: int = code
      if message and replacements:
        # Asterisk is used to unpack the values of the list
        self.message: str = f'{message.format(*replacements)}'
      elif message:
        self.message: str = message

  return Error

################################################################################
# ERROR CODES (https://google.github.io/glazier/error_codes)             #
################################################################################
GReservedError = _new_err(1337, 'Reserved {} {} {}')
GUncaughtError = _new_err(4000, 'Uncaught exception')
GCollectLogsError = _new_err(4301, 'Failed to collect logs')
GWebServerError = _new_err(5000, 'Failed to reach web server')
GServiceError = _new_err(5300, 'Service unavailable')
