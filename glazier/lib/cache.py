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

"""Manages the on-disk build cache."""

import os
import re
import typing
from typing import Optional

from glazier.lib import download
from glazier.lib import errors

if typing.TYPE_CHECKING:
  from glazier.lib import buildinfo


DNLD_RE = re.compile(r'([@|#][\S]+)')


class Error(errors.GlazierError):
  pass


class CacheError(Error):

  def __init__(self, file_path: str):
    super().__init__(
        error_code=errors.ErrorCode.CACHE_MISS,
        message=f'Unable to download required file: {file_path}')


class Cache(object):
  """Handles interation with the on-disk build cache."""

  def __init__(self):
    self._downloader = download.Download(show_progress=False)

  def _DestinationPath(self, cache_path: str, url: str) -> str:
    """Determines the local path for a file being downloaded.

    Args:
      cache_path: Path to the local build cache
      url: A web address to a file as a string

    Returns:
      The local disk path as a string.
    """
    file_name = url.split('/').pop()
    destination = os.path.join(cache_path + os.sep, file_name)
    return destination

  def _FindDownload(self, line: str) -> Optional[str]:
    """Searches a command line for any download strings.

    Args:
      line: the command line to search

    Returns:
      the url which requires downloading or none
    """
    result = DNLD_RE.search(line)
    if result:
      return result.group(1).rstrip('"\'')
    return None

  def CacheFromLine(self, line: str,
                    build_info: 'buildinfo.BuildInfo') -> Optional[str]:
    """Downloads any files in the command line and replaces with the local path.

    Args:
      line: the command line to process as a string
      build_info: the current build information

    Returns:
      the final command line as a string; None on error

    Raises:
      CacheError: unable to download a file to the local cache
    """
    match = self._FindDownload(line)
    while match:
      file_path = download.Transform(match, build_info)
      if download.IsRemote(file_path):
        destination = self._DestinationPath(build_info.CachePath(), file_path)
        try:
          self._downloader.DownloadFile(file_path, destination)
        except download.Error as e:
          self._downloader.PrintDebugInfo()
          raise CacheError(file_path) from e
      else:  # bypass download for local files
        destination = file_path
      line = line.replace(match, destination)
      match = self._FindDownload(line)
    return line
