# Copyright 2022 Google Inc. All Rights Reserved.
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
"""Handle graphics used during Glazier."""

import os

from glazier.lib.actions.base import BaseAction
from glazier.lib.actions.base import ValidationError

from glazier.lib import errors


class Error(errors.GlazierError):
  pass


class FileNotFound(Error):

  def __init__(self, path: str):
    super().__init__(
        error_code=errors.ErrorCode.FILE_NOT_FOUND,
        message=f'The following path does not exist: {path}')


class PrintFromFile(BaseAction):
  """Print text from a file at the specified path."""

  def Run(self):
    """Reads a file and prints the content."""
    path: str = self._args[0]
    ignore_error: bool = False

    if len(self._args) > 1:
      ignore_error = self._args[1]

    if not os.path.exists(path):
      if ignore_error:
        return
      raise FileNotFound(path)

    content = self._get_content(path)
    print(content)

  def _get_content(self, path: str):
    """Get content from the specified file.

    Args:
      path: The full path to the file.

    Returns:
      File content.

    Raises:
      FileNotFound: No file exists at the determined path.
    """
    f = open(path, 'r', encoding='utf-8')
    content = f.read()
    f.close()
    return content

  def Validate(self):
    self._TypeValidator(self._args, list)

    if not 1 <= len(self._args) <= 2:
      message = (f'Invalid PrintFromFile args "{self._args}" '
                 f'with length of {len(self._args)}')
      raise ValidationError(message)

    self._TypeValidator(self._args[0], str)
    if len(self._args) > 1:
      self._TypeValidator(self._args[1], bool)
