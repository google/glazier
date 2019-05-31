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

"""Actions for managing the local file systems."""

import logging
import os
import shutil
from glazier.lib.actions.base import ActionError
from glazier.lib.actions.base import BaseAction
from glazier.lib.actions.base import ValidationError  # pylint:disable=unused-import


class FileSystem(BaseAction):
  """Parent filesystem class with utility functions."""

  def _CreateDirectories(self, path):
    """Create a directory.

    Args:
      path: The full path to the directory to be created.

    Raises:
      ActionError: Failure creating the requested directory.
    """
    if not os.path.isdir(path):
      try:
        logging.debug('Creating directory: %s', path)
        os.makedirs(path)
      except (shutil.Error, OSError) as e:
        raise ActionError('Unable to create directory %s: %s' % (path, str(e)))


class CopyDir(FileSystem):
  """Copies directories on disk."""

  def Run(self):
    try:
      src = self._args[0]
      dst = self._args[1]
    except IndexError:
      raise ActionError('Unable to determine source and destination from %s.' %
                        str(self._args))
    try:
      logging.info('Copying directory: %s to %s', src, dst)
      shutil.copytree(src, dst)
    except (shutil.Error, OSError) as e:
      raise ActionError('Unable to copy %s to %s: %s' % (src, dst, str(e)))

  def Validate(self):
    self._ListOfStringsValidator(self._args, length=2)


class CopyFile(FileSystem):
  """Copies files on disk."""

  def Run(self):
    try:
      src = self._args[0]
      dst = self._args[1]
    except IndexError:
      raise ActionError('Unable to determine source and destination from %s.' %
                        str(self._args))
    try:
      path = os.path.dirname(dst)
      self._CreateDirectories(path)
      shutil.copy2(src, dst)
      logging.info('Copying: %s to %s', src, dst)
    except (shutil.Error, IOError) as e:
      raise ActionError('Unable to copy %s to %s: %s' % (src, dst, str(e)))

  def Validate(self):
    self._ListOfStringsValidator(self._args, length=2)


class MultiCopyFile(BaseAction):
  """Perform CopyFile on multiple sets of files."""

  def Run(self):
    try:
      for arg in self._args:
        cf = CopyFile([arg[0], arg[1]], self._build_info)
        cf.Run()
    except IndexError:
      raise ActionError('Unable to determine copy sets from %s.' %
                        str(self._args))

  def Validate(self):
    self._TypeValidator(self._args, list)
    for arg in self._args:
      cf = CopyFile(arg, self._build_info)
      cf.Validate()


class MkDir(FileSystem):
  """Create a directory."""

  def Run(self):
    try:
      path = self._args[0]
    except IndexError:
      raise ActionError('Unable to determine desired path from %s.' %
                        str(self._args))
    self._CreateDirectories(path)

  def Validate(self):
    self._ListOfStringsValidator(self._args)


class SetupCache(FileSystem):
  """Create the imaging cache directory."""

  def Run(self):
    path = self._build_info.CachePath()
    self._CreateDirectories(path)

  def Validate(self):
    self._TypeValidator(self._args, list)
