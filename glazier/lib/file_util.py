# python3
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

"""Utility functions for working with files and directories."""

import logging
import os
import shutil


class Error(Exception):
  pass


def Copy(src: str, dst: str):
  """Copy a file from src to dst.

  Args:
    src: The full file path to the source.
    dst: The full file path to the destination.

  Raises:
    Error: Failure copying the file.
  """
  try:
    CreateDirectories(dst)
    shutil.copy2(src, dst)
    logging.info('Copying: %s to %s', src, dst)
  except (shutil.Error, IOError) as e:
    raise Error('Unable to copy %s to %s: %s' % (src, dst, str(e)))


def CreateDirectories(path: str):
  """Create directory if the path to a file doesn't exist.

  Args:
    path: The full file path to where a file will be placed.

  Raises:
    Error: Failure creating the requested directory.
  """
  dirname = os.path.dirname(path)
  if not os.path.isdir(dirname):
    logging.debug('Creating directory %s ', dirname)
    try:
      os.makedirs(dirname)
    except (shutil.Error, OSError):
      raise Error('Unable to make directory: %s' % dirname)


def Move(src: str, dst: str):
  """Move a file from src to dst.

  Python's os.rename doesn't support overwrite on Windows.

  Args:
    src: The full file path to the source.
    dst: The full file path to the destination.

  Raises:
    Error: Failure moving the file.
  """
  try:
    Remove(dst)
    os.rename(src, dst)
  except OSError as e:
    raise Error('Failure moving file from %s to %s. (%s)' % (src, dst, str(e)))


def Remove(path: str):
  """Remove a file.

  Args:
    path: The full file path to the file to be removed.

  Raises:
    Error: Failure removing the file.
  """
  try:
    if os.path.exists(path):
      os.remove(path)
  except OSError as e:
    raise Error('Failure removing file %s. (%s)' % (path, str(e)))
