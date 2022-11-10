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
import hashlib
import logging
import os
import re
import socket
import ssl
import sys
import tempfile
import time

import typing
from typing import List, Optional
import urllib.request

from absl import flags
import backoff
from glazier.lib import beyondcorp
from glazier.lib import file_util
from glazier.lib import winpe

from glazier.lib import errors

if typing.TYPE_CHECKING:
  import http.client

CHUNK_BYTE_SIZE = 65536
SLEEP = 20

# Maximum amount of time to spend on all backoff retries, in seconds.
BACKOFF_MAX_TIME = 600

FLAGS = flags.FLAGS


class Error(errors.GlazierError):
  pass


class DownloadGiveUpError(Error):

  def __init__(self, tries: int, elapsed: float):
    super().__init__(
        error_code=errors.ErrorCode.DOWNLOAD_GIVE_UP,
        message=f'Failed after {tries} attempt(s) over {elapsed:0.1f} seconds')


class DownloadFailedError(Error):

  def __init__(self, url: str, code: int):
    super().__init__(
        error_code=errors.ErrorCode.DOWNLOAD_FAILED,
        message=f'Invalid return code [{code}] for file {url}')


class InvalidRemoteUrlError(Error):

  def __init__(self, url: str):
    super().__init__(
        error_code=errors.ErrorCode.DOWNLOAD_INVALID_REMOTE_URL,
        message=f'Invalid remote server URL "{url}".')


class LocalCopyError(Error):

  def __init__(self, src: str, dest: str):
    super().__init__(
        error_code=errors.ErrorCode.DOWNLOAD_LOCAL_COPY_ERROR,
        message=f'Unable to copy local file from {src} to {dest}')


class SignedUrlError(Error):

  def __init__(self, url: str):
    super().__init__(
        error_code=errors.ErrorCode.DOWNLOAD_SIGNED_URL_ERROR,
        message=f'Failed to obtain signed URL: {url}')


class MissingFileStreamError(Error):

  def __init__(self):
    super().__init__(
        error_code=errors.ErrorCode.DOWNLOAD_MISSING_FILE_STREAM,
        message='Cannot save to disk, missing file stream')


class StreamToDiskError(Error):

  def __init__(self, message: str):
    super().__init__(
        error_code=errors.ErrorCode.DOWNLOAD_STREAM_TO_DISK_ERROR,
        message=message)


class FileValidationError(Error):

  def __init__(self, message: str):
    super().__init__(
        error_code=errors.ErrorCode.DOWNLOAD_VALIDATION_ERROR,
        message=message)


# Required in order to patch BACKOFF_MAX_TIME to a more reasonable value in the
# unit tests. Passing a callable to the max_time argument of
# @backoff.on_exception() pushes the evaluation of that value to runtime,
# rather than at module load, which gives us time to modify BACKOFF_MAX_TIME
# during test setup.
def GetBackoffMaxTime():
  return BACKOFF_MAX_TIME


def BackoffGiveupHandler(details):
  raise DownloadGiveUpError(details['tries'], details['elapsed'])


def IsLocal(string: str) -> bool:
  return re.match(r'[A-Z,a-z]\:', string) is not None


def IsRemote(string: str) -> bool:
  return re.match(r'http(s)?:', string, re.I) is not None


def Transform(string: str, build_info) -> str:
  r"""Transforms abbreviated file names to absolute file paths.

  Short name support:
    #: A reference to the active release branch location.
    @: A reference to the binary storage root.
    \#: Escaped # character - replaced by # in string
    \@: Escaped @ character - replaced by @ in string
    %: A reference to the active release branch.
    \%: Escaped % character - replaced by % in string

  Args:
    string: The configuration string to be transformed.
    build_info: the current build information

  Returns:
    The adjusted file name string to be used in the manifest.
  """
  string = re.sub(r'(?<!\\)#', PathCompile(build_info) + '/', string)
  string = re.sub(r'\\#', '#', string)
  string = re.sub(r'(?<!\\)@', str(build_info.BinaryPath()), string)
  string = re.sub(r'\\@', '@', string)
  string = re.sub(r'(?<!\\)%', str(build_info.Branch()), string)
  string = re.sub(r'\\%', '%', string)
  return string


def PathCompile(build_info,
                file_name: Optional[str] = None,
                base: Optional[str] = None) -> str:
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


class BaseDownloader(object):
  """Downloads files over HTTPS."""

  def __init__(self, show_progress: bool = False):
    self._debug_info = {}
    self._save_location = None
    self._default_show_progress = show_progress
    self._ca_cert_file = None
    self._beyondcorp = beyondcorp.BeyondCorp()

  def _ConvertBytes(self, num_bytes: int) -> str:
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
    return [urllib.request.HTTPSHandler()]

  def _InstallOpeners(self):
    opener = urllib.request.OpenerDirector()
    for handler in self._GetHandlers():
      opener.add_handler(handler)
    urllib.request.install_opener(opener)

  @backoff.on_exception(
      backoff.expo,
      (urllib.error.HTTPError, urllib.error.URLError),
      max_time=GetBackoffMaxTime,
      on_giveup=BackoffGiveupHandler)
  def _OpenFileStream(
      self,
      url: str,
      status_codes: Optional[List[int]] = None) -> 'http.client.HTTPResponse':
    """Opens a connection to a remote resource, with retries.

    Args:
      url: The address of the file to be downloaded.
      status_codes: A list of acceptable status codes to be returned by the
        remote endpoint.

    Returns:
      file_stream: urlopen's file stream

    Raises:
      DownloadFailedError: The resource was unreachable or failed to return with
        the expected code.
    """
    if status_codes:
      logging.info('Expected status code(s): %s', status_codes)

    try:
      if winpe.check_winpe():
        file_stream = urllib.request.urlopen(url, cafile=self._ca_cert_file)
      else:
        file_stream = urllib.request.urlopen(url)

    # First attempt failed with HTTPError. Reraise and trigger a retry.
    except urllib.error.HTTPError:
      logging.error('File not found on remote server: %s.', url)
      raise

    # First attempt failed with URLError. Try something else before giving up.
    except urllib.error.URLError as e1:
      logging.error('Error while downloading "%s": %s', url, e1)

      try:
        logging.info('Trying again with machine context...')
        ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        file_stream = urllib.request.urlopen(url, context=ctx)

      # Second attempt failed with HTTPError. Reraise and trigger a retry.
      except urllib.error.HTTPError:
        logging.error('File not found on remote server: %s.', url)
        raise

      # Second attempt failed with URLError. Reraise and trigger a retry.
      except urllib.error.URLError as e2:
        logging.error('Error while downloading "%s": %s', url, e2)
        raise

    # We successfully retrieved a file stream, so just return it.
    if file_stream.getcode() in (status_codes or [200]):
      return file_stream

    # In the case of a redirection, just call into _OpenFileStream() again with
    # the redirect URL.
    elif file_stream.getcode() in [302]:
      return self._OpenFileStream(file_stream.geturl(), status_codes)

    # For anything else, fail permanently with a DownloadError.
    else:
      raise DownloadFailedError(url, file_stream.getcode())

  def _OpenStream(
      self,
      url: str,
      status_codes: Optional[List[int]] = None) -> 'http.client.HTTPResponse':
    """Opens a connection to a remote resource.

    Args:
      url:  The address of the file to be downloaded.
      status_codes: A list of acceptable status codes to be returned by the
        remote endpoint.

    Returns:
      file_stream: urlopen's file stream

    Raises:
      InvalidRemoteUrlError: The resource was unreachable or failed to return
        with the expected code.
    """
    self._InstallOpeners()

    url = url.strip()
    parsed = urllib.parse.urlparse(url)
    if not parsed.netloc:
      raise InvalidRemoteUrlError(url)

    return self._OpenFileStream(url, status_codes)

  def CheckUrl(self, url: str, status_codes: List[int]) -> bool:
    """Check a remote URL for availability.

    Args:
      url: A URL to access.
      status_codes: Acceptable status codes for the connection (list).

    Returns:
      True if accessing the file produced one of status_codes.
    """
    logging.info('Checking URL: %s', url)

    try:
      self._OpenStream(url, status_codes=status_codes)
      return True
    except Error as e:
      logging.error(e)
    return False

  def DownloadFile(self,
                   url: str,
                   save_location: str,
                   show_progress: bool = False):
    """Downloads a file from one location to another.

    If URL references a local path, the file will be copied rather than
    downloaded.

    Args:
      url:  The address of the file to be downloaded.
      save_location: The full path of where the file should be saved.
      show_progress: Print download progress to stdout (overrides default).

    Raises:
      LocalCopyError: failure writing file to the save_location
    """
    logging.info('Downloading file: %s', url)

    self._save_location = save_location
    if IsRemote(url):
      if self._beyondcorp.CheckBeyondCorp():
        url = self._SetUrl(url)
      file_stream = self._OpenStream(url)
      self._StreamToDisk(file_stream, show_progress)
    else:
      try:
        file_util.Copy(url, save_location)
      except file_util.Error as e:
        raise LocalCopyError(url, save_location) from e

  def DownloadFileTemp(self, url: str, show_progress: bool = False) -> str:
    """Downloads a file to temporary storage.

    Args:
      url:  The address of the file to be downloaded.
      show_progress: Print download progress to stdout (overrides default).

    Returns:
      A string containing a path to the temporary file.
    """
    logging.info('Downloading temp file: %s', url)

    destination = tempfile.NamedTemporaryFile()
    self._save_location = destination.name
    destination.close()
    if self._beyondcorp.CheckBeyondCorp():
      url = self._SetUrl(url)
    file_stream = self._OpenStream(url)
    self._StreamToDisk(file_stream, show_progress)
    return self._save_location

  def _DownloadChunkReport(self, bytes_so_far: int, total_size: int):
    """Prints download progress information.

    Args:
      bytes_so_far:  The number of bytes downloaded so far.
      total_size:  The total size of the file being downloaded.
    """
    percent = float(bytes_so_far) / total_size
    percent = round(percent * 100, 2)
    message = (('\rDownloaded %s of %s (%0.2f%%)' +
                (' ' * 10)) % (self._ConvertBytes(bytes_so_far),
                               self._ConvertBytes(total_size), percent))
    sys.stdout.write(message)
    sys.stdout.flush()

    if bytes_so_far >= total_size:
      sys.stdout.write('\n')

  def _SetUrl(self, url: str) -> str:
    """Simple helper function to determine signed URL.

    Args:
      url: the url we want to download from.

    Returns:
      A string with the applicable URLs

    Raises:
      SignedUrlError: Failed to obtain SignedURL.
    """
    if not FLAGS.use_signed_url:
      return url

    try:
      if url.startswith(FLAGS.binary_server):
        url = url.replace(f'{FLAGS.binary_server}/', '')
      if url.startswith(FLAGS.config_server):
        url = url.replace(f'{FLAGS.config_server}/', '')
      return self._beyondcorp.GetSignedUrl(url)
    except beyondcorp.Error as e:
      raise SignedUrlError(url) from e

  def _StoreDebugInfo(self,
                      file_stream: 'http.client.HTTPResponse',
                      socket_error: Optional[str] = None):
    """Gathers debug information for use when file downloads fail.

    Args:
      file_stream:  The file stream object of the file being downloaded.
      socket_error: Store the error raised from the socket class with other
        debug info.
    """
    if socket_error:
      self._debug_info['socket_error'] = socket_error
    if file_stream:
      for header in file_stream.info().items():
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

  @backoff.on_exception(
      backoff.expo,
      AttributeError,
      max_time=GetBackoffMaxTime,
      on_giveup=BackoffGiveupHandler)
  def _GetFileStreamSize(self, file_stream: 'http.client.HTTPResponse'):
    url = file_stream.geturl()
    total_size = int(file_stream.headers.get('Content-Length').strip())
    return (url, total_size)

  def _StreamToDisk(self,
                    file_stream: 'http.client.HTTPResponse',
                    show_progress: bool = None):
    """Save a file stream to disk.

    Args:
      file_stream: The file stream returned by a successful urlopen()
      show_progress: Print download progress to stdout (overrides default).

    Raises:
      Error: Error retrieving file or saving to disk.
    """
    progress = self._default_show_progress
    if show_progress is not None:
      progress = show_progress

    if file_stream is None:
      raise MissingFileStreamError()

    bytes_so_far = 0
    url, total_size = self._GetFileStreamSize(file_stream)

    try:
      with open(self._save_location, 'wb') as output_file:
        logging.info('Downloading file "%s" to "%s".',
                     url.split('?')[0], self._save_location)
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
      raise StreamToDiskError('Socket error during download.') from e
    except IOError as e:
      message = (
          f'File location could not be opened for writing: '
          f'{self._save_location}')
      raise StreamToDiskError(message) from e
    self._Validate(file_stream, total_size)
    file_stream.close()

  def _Validate(self, file_stream: 'http.client.HTTPResponse',
                expected_size: int):
    """Validate the downloaded file.

    Args:
      file_stream: The file stream returned by a successful urlopen()
      expected_size:  The total size of the file being downloaded.

    Raises:
      FileValidationError: File failed validation.
    """
    if not os.path.exists(self._save_location):
      self._StoreDebugInfo(file_stream)
      raise FileValidationError(
          f'Could not locate file at {self._save_location}')

    actual_file_size = os.path.getsize(self._save_location)
    if actual_file_size != expected_size:
      self._StoreDebugInfo(file_stream)
      message = (
          f'File size of {actual_file_size} bytes did not match expected size '
          f'of {expected_size}!')
      raise FileValidationError(message)

  def VerifyShaHash(self, file_path: str, expected: str) -> bool:
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
