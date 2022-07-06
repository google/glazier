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

"""Actions for stopping the image."""

import logging
import re
from glazier.lib import interact
from glazier.lib.actions.base import ActionError
from glazier.lib.actions.base import BaseAction
from glazier.lib.actions.base import ValidationError


class Abort(BaseAction):
  """Abort imaging with a custom message."""

  def Run(self):
    message = self._args[0]
    raise ActionError(message)

  def Validate(self):
    if not isinstance(self._args, list):
      raise ValidationError(
          f'Invalid args type ({type(self._args)}): {self._args}')
    if len(self._args) != 1:
      raise ValidationError(f'Invalid args length: {len(self._args)}')
    if not isinstance(self._args[0], str):
      raise ValidationError(f'Invalid argument type: {self._args[0]}')


class Warn(BaseAction):
  """Warn the user about a problem condition, and ask whether to continue."""

  def Run(self):
    print('\n\n%s\n\n' % str(self._args[0]))
    response = interact.Prompt('Do you still want to proceed (y/n)? ')
    if not response or not re.match(r'^[Yy](es)?$', response):
      raise ActionError('User chose not to continue installation.')
    logging.info('User chose to continue installation despite warning.')

  def Validate(self):
    if not isinstance(self._args, list):
      raise ValidationError(
          f'Invalid args type ({type(self._args)}): {self._args}')
    if len(self._args) != 1:
      raise ValidationError(f'Invalid args length: {self._args}')
    if not isinstance(self._args[0], str):
      raise ValidationError(f'Invalid argument type: {type(self._args[0])}')
