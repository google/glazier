# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Construct and set the current console title."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import os
from typing import Optional

from glazier.lib import buildinfo
from glazier.lib import constants
from glazier.lib import stage
from glazier.lib import winpe

from glazier.lib import errors


class Error(errors.GlazierError):
  pass


class CannotSetConsoleTitleError(Error):

  def __init__(self):
    super().__init__(
        error_code=errors.ErrorCode.CANNOT_SET_CONSOLE_TITLE,
        message='Failed to set console title')


def _base_title() -> Optional[str]:
  """Concatenate base values for the title based on build information.

  Returns:
    The base text for the title as a string.
  """
  build_info = buildinfo.BuildInfo()
  getid = build_info.ImageID()
  getrelease = build_info.Release()
  getstage = stage.get_active_stage()
  base = []

  if winpe.check_winpe():
    base.append('WinPE')
  if constants.FLAGS.config_root_path:
    # Existence of the constant must be checked before strip to avoid null error
    path = constants.FLAGS.config_root_path.strip('/')
    if path:
      base.append(path)
  if getstage:
    base.append(f'Stage: {getstage}')
  if getrelease:
    base.append(getrelease)
  if getid:
    base.append(getid)

  # Convert list to a string, using map() to account for nonetypes
  return ' - '.join(map(str, base))


def _build_title(string: Optional[str] = None) -> str:
  """Concatenate strings to construct the console title.

  Args:
    string: Optional string to add to the console title.

  Returns:
    The constructed console title as a string.
  """
  prefix = 'Glazier'
  base = _base_title()
  title = []

  if string:
    title.append(string)
  if base:
    title.append(base)

  if title:
    title = ' - '.join(map(str, title))
    return ''.join(prefix + ' [' + title + ']')

  return prefix


def set_title(string: Optional[str] = None) -> str:
  """Set the console title.

  Args:
    string: Optional string to add to the console title.

  Returns:
    Title as a string.
  """
  title = _build_title(string)
  try:
    os.system(f'title {title}')
    logging.debug('Set console title: %s', title)
    return title
  except OSError as e:
    raise CannotSetConsoleTitleError() from e
