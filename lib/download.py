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

"""Download files over HTTPS.

> Resource Requirements

  * resources/ca_certs.crt
      A certificate file containing permitted root certs for SSL validation.

"""

from __future__ import absolute_import
from __future__ import print_function

import hashlib
import logging
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
import urllib2

CHUNK_BYTE_SIZE = 65536


def Transform(string, build_info):
  """Transforms abbreviated file names to absolute file paths.

  Short name support:
    #: A reference to the active release branch location.
    @: A reference to the binary storage root.

  Args:
    string: The configuration string to be transformed.
    build_info: the current build information

  Returns:
    The adjusted file name string to be used in the manifest.
  """
  if '#' in string:
    string = string.replace('#', '%s/' % PathCompile(build_info))
  if '@' in string:
    string = string.replace('@', str(build_info.BinaryPath()))
  return string


def PathCompile(build_info, file_name=None, base=None):
  """Compile the active path from the base path and the active conf path.

    Attempt to do a reasonable job of joining path components with single
    slashes.

    The three main parts considered are the _base_url (or base arg), any
    subdirectories from _conf_path, and the optional file name arg.  These are
    combined into [https://base.url][/conf/path/parts][/filename.ext]

    We attempt to strip trailing slashes, so paths without a filename return
    with no trailing /.

  Args:
    build_info: the current build information
    file_name: append a filename to the path
    base: use a non-default base path

  Returns:
    The compiled URL as a string.
  """
  path = base
  if not path:
    path = build_info.ReleasePath()

  path = path.rstrip('/')

  sub_path = build_info.ActiveConfigPath()
  if sub_path:
    path += '/'
    sub_path = '/'.join(sub_path).strip('/')
    path += sub_path

  if file_name:
    path += '/'
    file_name = file_name.lstrip('/')
    path += file_name

  return path


class DownloadError(Exception):
  """The transfer of the file failed."""
  pass


class BaseDownloader(object):
  """Downloads files over HTTPS."""

  def __init__(self, show_progress=False):
    self._debug_info = {}
    self._save_location = None
    self._default_show_progress = show_progress

  def _ConvertBytes(self, num_bytes):
    """Converts number of bytes to a human readable format.

    Args:
      num_bytes: The number to convert to a more human readable format (int).

    Returns:
      size: The number of bytes in human readable format (string).
    """
    num_bytes = float(num_bytes)
    if num_bytes >= 1099511627776:
      terabytes = num_bytes / 1099511627776
      size = '%.2fTB' % terabytes
    elif num_bytes >= 1073741824:
      gigabytes = num_bytes / 1073741824
      size = '%.2fGB' % gigabytes
    elif num_bytes >= 1048576:
      megabytes = num_bytes / 1048576
      size = '%.2fMB' % megabytes
    elif num_bytes >= 1024:
      kilobytes = num_bytes / 1024
      size = '%.2fKB' % kilobytes
    else:
      size = '%.2fB' % num_bytes
    return size

  def _GetHandlers(self):
    return [urllib2.HTTPSHandler()]

  def _DownloadFile(self, url, max_retries=5, show_progress=None):
    """Downloads a file from and saves it to the specified location.

    Args:
      url:  The address of the file to be downloaded.
      max_retries:  The number of times to attempt to download
        a file if the first attempt fails.
      show_progress: Print download progress to stdout (overrides default).

    Raises:
      DownloadError: The downloaded file did not match the expected file
        size.
    """
    attempt = 0
    file_stream = None

    opener = urllib2.OpenerDirector()
    for handler in self._GetHandlers():
      opener.add_handler(handler)
    urllib2.install_opener(opener)

    while True:
      try:
        attempt += 1
        file_stream = urllib2.urlopen(url)
      except urllib2.HTTPError:
        logging.error('File not found on remote server: %s.', url)
      except urllib2.URLError as e:
        logging.error('Error connecting to remote server to download file '
                      '"%s". The error was: %s', url, e)
      if file_stream:
        if file_stream.getcode() in [200]:
          break
        else:
          raise DownloadError('Invalid return code for file %s. [%d]' %
                              (url, file_stream.getcode()))

      if attempt < max_retries:
        logging.info('Sleeping for 20 seconds and then retrying the download.')
        time.sleep(20)
      else:
        raise DownloadError('Permanent download failure for file %s.' % url)

    self._StreamToDisk(file_stream, show_progress)

  def DownloadFile(self, url, save_location, max_retries=5, show_progress=None):
    """Downloads a file to temporary storage.

    Args:
      url:  The address of the file to be downloaded.
      save_location: The full path of where the file should be saved.
      max_retries:  The number of times to attempt to download
        a file if the first attempt fails.
      show_progress: Print download progress to stdout (overrides default).
    """
    self._save_location = save_location
    self._DownloadFile(url, max_retries, show_progress)

  def DownloadFileTemp(self, url, max_retries=5, show_progress=None):
    """Downloads a file to temporary storage.

    Args:
      url:  The address of the file to be downloaded.
      max_retries:  The number of times to attempt to download
        a file if the first attempt fails.
      show_progress: Print download progress to stdout (overrides default).

    Returns:
      A string containing a path to the temporary file.
    """
    destination = tempfile.NamedTemporaryFile()
    self._save_location = destination.name
    destination.close()
    self._DownloadFile(url, max_retries, show_progress)
    return self._save_location

  def _DownloadChunkReport(self, bytes_so_far, total_size):
    """Prints download progress information.

    Args:
      bytes_so_far:  The number of bytes downloaded so far.
      total_size:  The total size of the file being downloaded.
    """
    percent = float(bytes_so_far) / total_size
    percent = round(percent * 100, 2)
    message = (('\rDownloaded %s of %s (%0.2f%%)' + (' ' * 10)) %
               (self._ConvertBytes(bytes_so_far),
                self._ConvertBytes(total_size), percent))
    sys.stdout.write(message)
    sys.stdout.flush()

    if bytes_so_far >= total_size:
      sys.stdout.write('\n')

  def _StoreDebugInfo(self, file_stream, socket_error=None):
    """Gathers debug information for use when file downloads fail.

    Args:
      file_stream:  The file stream object of the file being downloaded.
      socket_error: Store the error raised from the socket class with
        other debug info.

    Returns:
      debug_info:  A dictionary containing various pieces of debugging
          information.
    """
    if socket_error:
      self._debug_info['socket_error'] = socket_error
    if file_stream:
      for header in file_stream.info().header_items():
        self._debug_info[header[0]] = header[1]
    self._debug_info['current_time'] = time.strftime(
        '%A, %d %B %Y %H:%M:%S UTC')

  def PrintDebugInfo(self):
    """Print the debugging information to the screen."""
    if self._debug_info:
      print('\n\n\n\n')
      print('---------------')
      print('Debugging info: ')
      print('---------------')
      for key, value in self._debug_info.items():
        print('%s: %s' % (key, value))
      print('\n\n\n')

  def _StreamToDisk(self, file_stream, show_progress=None):
    """Save a file stream to disk.

    Args:
      file_stream: The file stream returned by a successful urlopen()
      show_progress: Print download progress to stdout (overrides default).

    Raises:
      DownloadError: Error retrieving file or saving to disk.
    """
    progress = self._default_show_progress
    if show_progress is not None:
      progress = show_progress
    bytes_so_far = 0
    url = file_stream.geturl()
    total_size = int(file_stream.info().getheader('Content-Length').strip())
    try:
      with open(self._save_location, 'wb') as output_file:
        logging.info('Downloading file "%s" to "%s".', url, self._save_location)
        while 1:
          chunk = file_stream.read(CHUNK_BYTE_SIZE)
          bytes_so_far += len(chunk)
          if not chunk:
            break
          output_file.write(chunk)
          if progress:
            self._DownloadChunkReport(bytes_so_far, total_size)
    except socket.error as e:
      self._StoreDebugInfo(file_stream, str(e))
      raise DownloadError('Socket error during download.')
    except IOError:
      raise DownloadError('File location could not be opened for writing: %s' %
                          self._save_location)
    self._Validate(file_stream, total_size)
    file_stream.close()

  def _Validate(self, file_stream, expected_size):
    """Validate the downloaded file.

    Args:
      file_stream: The file stream returned by a successful urlopen()
      expected_size:  The total size of the file being downloaded.

    Raises:
      DownloadError: File failed validation.
    """
    if not os.path.exists(self._save_location):
      self._StoreDebugInfo(file_stream)
      raise DownloadError('Could not locate file at %s' % self._save_location)

    actual_file_size = os.path.getsize(self._save_location)
    if actual_file_size != expected_size:
      self._StoreDebugInfo(file_stream)
      message = ('File size of %s bytes did not match expected size of %s!',
                 actual_file_size, expected_size)
      raise DownloadError(message)

  def VerifyShaHash(self, file_path, expected):
    """Verifies the SHA256 hash of a file.

    Arguments:
      file_path: The path to the file that will be checked.
      expected: The expected SHA hash as a string.

    Returns:
      True if the calculated hash matches the expected hash.
      False if the calculated hash does not match the expected hash or if there
          was an error reading the file or the SHA file.
    """
    sha_object = hashlib.new('sha256')

    # Read the file in 4MB chunks to avoid running out of memory
    # while processing very large files.
    try:
      with open(file_path, 'rb') as f:
        while True:
          current_chunk = f.read(4194304)
          if not current_chunk:
            break
          sha_object.update(current_chunk)
    except IOError:
      logging.error('Unable to read file %s for SHA verification.', file_path)
      return False

    file_hash = sha_object.hexdigest()
    expected = expected.lower()

    if file_hash == expected:
      logging.info('SHA256 hash for %s matched expected hash of %s.', file_path,
                   expected)
      return True
    else:
      logging.error(
          'SHA256 hash for %s was %s, which did not match expected hash of %s.',
          file_path, file_hash, expected)
      return False


# Set our downloader of choice
Download = BaseDownloader

