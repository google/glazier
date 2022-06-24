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

"""Provide access to non-Python installer resource files."""

import os
# do not remove: internal placeholder 1
from absl import flags

from glazier.lib import errors

FLAGS = flags.FLAGS
flags.DEFINE_string(
    'resource_path', '', 'Path to top level installer resource file storage.')


class Error(errors.GlazierError):
  pass


class FileNotFound(Error):

  def __init__(self, path: str):
    super().__init__(
        error_code=errors.ErrorCode.FILE_NOT_FOUND,
        message=f'The following path does not exist: {path}')


class Resources(object):

  def __init__(self, resource_dir=None):
    self._path = resource_dir
    if not self._path:
      self._path = FLAGS.resource_path
    if not self._path:
      path = os.path.dirname(os.path.realpath(__file__))
      self._path = os.path.join(path, 'resources')

  def GetResourceFileName(self, file_name):
    """Returns the full path to a resource file.

    Args:
      file_name: A file to search for under the installer resource directory.

    Returns:
      The full path to the resource on disk.

    Raises:
      FileNotFound: No file exists at the determined path.
    """
    file_name = file_name.strip('/')
    path = os.path.join(self._path, file_name)

    if os.path.exists(path):
      return path
    raise FileNotFound(path)
