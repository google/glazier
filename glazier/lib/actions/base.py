# Copyright 2016 Google Inc. All Rights Reserved.
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

"""Generic imaging action class."""

import logging
from typing import Optional

from glazier.lib import errors


class ActionError(errors.GlazierError):
  """Failure completing requested action."""

  def __init__(self, message: Optional[str] = None):

    if message is None:
      message = 'Error encountered while executing action'

    super().__init__(
        error_code=errors.ErrorCode.ACTION_ERROR,
        message=message)


class ValidationError(errors.GlazierError):
  """Failure validating a command type."""

  def __init__(self, message: str):
    super().__init__(
        error_code=errors.ErrorCode.VALIDATION_ERROR,
        message=message)


class BaseAction(object):
  """Generic action type."""

  def __init__(self, args, build_info):
    self._args = args
    self._build_info = build_info
    self._realtime = False
    self._Setup()

  def IsRealtime(self):
    """Run the action on discovery rather than queueing in the task list."""
    return self._realtime

  def Run(self):
    """Override this function to implement a new action."""
    pass

  def _Setup(self):
    """Override to customize action on initialization."""
    pass

  def Validate(self):
    """Override this function to implement validation of actions."""
    logging.warning('Validation not implemented for action %s.',
                    self.__class__.__name__)

  def _ListOfStringsValidator(self, args, length=1, max_length=None):
    if not max_length:
      max_length = length
    self._TypeValidator(args, list)
    if not length <= len(args) <= max_length:
      raise ValidationError('Invalid args length: %s' % args)
    for arg in args:
      self._TypeValidator(arg, str)

  def _TypeValidator(self, args, expect_types):
    if not isinstance(args, expect_types):
      raise ValidationError('Invalid type for arg %s. Found: %s, Expected: %s' %
                            (args, type(args), str(expect_types)))
