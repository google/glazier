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
from glazier.lib import download
from glazier.lib import file_util
import yaml


class Error(Exception):
  pass


def Dump(path, data, mode='w'):
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
    raise Error('Could not save data to yaml file %s: %s' % (path, str(e)))
  # Replace the original with the tmp.
  try:
    file_util.Move(tmp_f, path)
  except file_util.Error as e:
    raise Error('Could not replace config file. (%s)' % str(e))


def Read(path):
  """Read a config file at path and return any data it contains.

  Will attempt to download files from remote repositories prior to reading.

  Args:
    path: The path (either local or remote) to read from.

  Returns:
    The parsed YAML content from the file.

  Raises:
    Error: Failure retrieving a remote file or parsing file content.
  """
  if re.match('^http(s)?://', path):
    downloader = download.Download()
    try:
      path = downloader.DownloadFileTemp(path)
    except download.DownloadError as e:
      raise Error('Could not download yaml file %s: %s' % (path, str(e)))
  return _YamlReader(path)


def _YamlReader(path):
  """Read a configuration file and return the contents.

  Can be overloaded to read configs from different sources.

  Args:
    path: The config file name (eg build.yaml).

  Returns:
    The parsed content of the yaml file.
  """
  try:
    with open(path, 'r') as yaml_file:
      yaml_config = yaml.safe_load(yaml_file)
  except IOError as e:
    raise Error('Could not read yaml file %s: %s' % (path, str(e)))
  return yaml_config
