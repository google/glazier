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

"""Functions for interacting with yaml configuration files."""

import re
from typing import Any
from glazier.lib import file_util
import yaml

from glazier.lib import download
from glazier.lib import errors


def Remove(path: str, backup: bool = True):
  """Remove a config file.

  Args:
    path: The filesystem path to the file.
    backup: Whether to make a backup of the file being removed.

  Raises:
    Error: Failure performing the filesystem operation.
  """
  if backup:
    src = path
    dest = path + '.bak'
    try:
      file_util.Move(src, dest)
    except file_util.Error as e:
      raise errors.FileMoveError(src, dest) from e
  else:
    try:
      file_util.Remove(path)
    except file_util.Error as e:
      raise errors.FileRemoveError(path) from e


def Dump(path: str, data: Any, mode: str = 'w'):
  """Write a config file containing some data.

  Args:
    path: The filesystem path to the destination file.
    data: Data to be written to the file as yaml.
    mode: Mode to use for writing the file (default: w)
  """
  file_util.CreateDirectories(path)
  tmp_f = path + '.tmp'

  # Write to a .tmp file to avoid corrupting the original if aborted mid-way.
  try:
    with open(tmp_f, mode) as handle:
      handle.write(yaml.dump(data))
  except IOError as e:
    raise errors.FileWriteError(path) from e

  # Replace the original with the tmp.
  try:
    file_util.Move(tmp_f, path)
  except file_util.Error as e:
    raise errors.FileMoveError(tmp_f, path) from e


def Read(path: str):
  """Read a config file at path and return any data it contains.

  Will attempt to download files from remote repositories prior to reading.

  Args:
    path: The path (either local or remote) to read from.

  Returns:
    The parsed YAML content from the file.

  Raises:
    DownloadError: Failure retrieving a remote file or
    FileReadError: Failure parsing file content.
  """
  if re.match('^http(s)?://', path):
    downloader = download.Download()
    path = downloader.DownloadFileTemp(path)
  return _YamlReader(path)


def _YamlReader(path: str) -> str:
  """Read a configuration file and return the contents.

  Can be overloaded to read configs from different sources.

  Args:
    path: The config file name (eg build.yaml).

  Returns:
    The parsed content of the yaml file.

  Raises:
    FileReadError: Failure parsing the file content.
  """
  try:
    with open(path, 'r') as yaml_file:
      yaml_config = yaml.safe_load(yaml_file)
  except IOError as e:
    raise errors.FileReadError(path) from e
  return yaml_config
