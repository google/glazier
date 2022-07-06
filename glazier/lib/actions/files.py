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

"""Actions for interacting with files (text, zip, exe, etc)."""

import logging
import shlex
from typing import List
import zipfile
from glazier.lib import cache
from glazier.lib import events
from glazier.lib import execute
from glazier.lib import file_util
from glazier.lib.actions.base import ActionError
from glazier.lib.actions.base import BaseAction
from glazier.lib.actions.base import ValidationError

from glazier.lib import download


class Execute(BaseAction):
  """Run an executable."""

  def _Run(self, command: str, success_codes: List[int],
           reboot_codes: List[int], restart_retry: bool, shell: bool):
    logging.debug('Interpreting command: %s', command)
    try:
      command_cache = cache.Cache().CacheFromLine(command, self._build_info)
    except cache.Error as e:
      raise ActionError() from e

    try:
      command_list = shlex.split(command_cache, posix=False)
      result = execute.execute_binary(
          command_list[0],
          command_list[1:],
          success_codes + reboot_codes,
          shell=shell)
    except (execute.Error, ValueError) as e:
      raise ActionError() from e
    except KeyboardInterrupt as e:
      raise ActionError('KeyboardInterrupt detected, exiting.') from e

    if result in reboot_codes:
      raise events.RestartEvent(
          'Restart triggered by exit code: %d' % result,
          5,
          retry_on_restart=restart_retry)
    elif result not in success_codes:
      raise ActionError(f'Command returned invalid exit code: {result}')

  def Run(self):
    for cmd in self._args:
      command = cmd[0]
      success_codes = cmd[1] if len(cmd) > 1 else [0]
      reboot_codes = cmd[2] if len(cmd) > 2 else []
      restart_retry = cmd[3] if len(cmd) > 3 else False
      shell = cmd[4] if len(cmd) > 4 else False
      self._Run(command, success_codes, reboot_codes, restart_retry, shell)

  def Validate(self):
    self._TypeValidator(self._args, list)
    for cmd_arg in self._args:
      self._TypeValidator(cmd_arg, list)
      if not 1 <= len(cmd_arg) <= 5:
        raise ValidationError(f'Invalid args length: {len(cmd_arg)}')
      self._TypeValidator(cmd_arg[0], str)  # cmd
      if len(cmd_arg) > 1:  # success codes
        self._TypeValidator(cmd_arg[1], list)
        for arg in cmd_arg[1]:
          self._TypeValidator(arg, int)
      if len(cmd_arg) > 2:  # reboot codes
        self._TypeValidator(cmd_arg[2], list)
        for arg in cmd_arg[2]:
          self._TypeValidator(arg, int)
      if len(cmd_arg) > 3:  # retry on restart
        self._TypeValidator(cmd_arg[3], bool)
      if len(cmd_arg) > 4:  # shell
        self._TypeValidator(cmd_arg[4], bool)


class Get(BaseAction):
  """Download a file from a remote source."""

  def Run(self):
    downloader = download.Download()
    for arg in self._args:
      src = arg[0]
      dst = arg[1]
      full_url = download.Transform(src, self._build_info)
      # support legacy untagged short filenames
      if not (download.IsRemote(full_url) or download.IsLocal(full_url)):
        full_url = download.PathCompile(self._build_info, file_name=full_url)
      try:
        file_util.CreateDirectories(dst)
      except file_util.Error as e:
        raise ActionError(
            f'Could not create destination directory: {dst}') from e
      try:
        downloader.DownloadFile(full_url, dst, show_progress=True)
      except download.Error as e:
        downloader.PrintDebugInfo()
        raise ActionError(f'Transfer error while downloading {full_url}') from e
      if len(arg) > 2 and arg[2]:
        logging.info('Verifying SHA256 hash for %s.', dst)
        hash_ok = downloader.VerifyShaHash(dst, arg[2])
        if not hash_ok:
          raise ActionError(f'SHA256 hash for {dst} was incorrect.')

  def Validate(self):
    self._TypeValidator(self._args, list)
    for arg in self._args:
      self._ListOfStringsValidator(arg, 2, 3)


class Unzip(BaseAction):
  """Unzip a zip archive to the local filesystem."""

  def Run(self):
    try:
      zip_file = self._args[0]
      out_path = self._args[1]
    except IndexError as e:
      raise ActionError(
          f'Unable to determine desired paths from {self._args}.') from e

    try:
      file_util.CreateDirectories(out_path)
    except file_util.Error as e:
      raise ActionError(f'Unable to create output path {out_path}.') from e

    try:
      zf = zipfile.ZipFile(zip_file)
      zf.extractall(out_path)
    except (IOError, zipfile.BadZipfile) as e:
      raise ActionError('Bad zip file given as input.') from e

  def Validate(self):
    self._ListOfStringsValidator(self._args, 2)
