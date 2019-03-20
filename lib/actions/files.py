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
import subprocess
import time
import zipfile
from glazier.lib import cache
from glazier.lib import download
from glazier.lib import file_util
from glazier.lib.actions.base import ActionError
from glazier.lib.actions.base import BaseAction
from glazier.lib.actions.base import RestartEvent
from glazier.lib.actions.base import ValidationError


class Execute(BaseAction):
  """Run an executable."""

  def _Run(self, command, success_codes, reboot_codes, restart_retry):
    c = cache.Cache()
    logging.debug('Interpreting command %s', command)
    try:
      command = c.CacheFromLine(command, self._build_info)
    except cache.CacheError as e:
      raise ActionError(e)
    logging.info('Executing command %s', command)
    try:
      output = ''
      err = ''
      result = subprocess.Popen(command,
                                shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
      output, err = result.communicate()
    except WindowsError as e:  # pylint: disable=undefined-variable
      raise ActionError('Failed to execute command %s (%s)' % (command, str(e)))
    except KeyboardInterrupt:
      logging.debug('Child received KeyboardInterrupt. Ignoring.')

    if output:
      logging.info(output)
    if err:
      logging.error(err)

    if result.returncode in reboot_codes:
      raise RestartEvent(
          'Restart triggered by exit code %d' % result.returncode,
          5,
          retry_on_restart=restart_retry)
    elif result.returncode not in success_codes:
      raise ActionError('Command returned invalid exit code %d' %
                        result.returncode)
    time.sleep(5)

  def Run(self):
    for cmd in self._args:
      command = cmd[0]
      success_codes = [0]
      reboot_codes = []
      restart_retry = False
      if len(cmd) > 1 and cmd[1]:
        success_codes = cmd[1]
      if len(cmd) > 2 and cmd[2]:
        reboot_codes = cmd[2]
      if len(cmd) > 3:
        restart_retry = cmd[3]
      self._Run(command, success_codes, reboot_codes, restart_retry)

  def Validate(self):
    self._TypeValidator(self._args, list)
    for cmd_arg in self._args:
      self._TypeValidator(cmd_arg, list)
      if not 1 <= len(cmd_arg) <= 4:
        raise ValidationError('Invalid args length: %s' % cmd_arg)
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


class Get(BaseAction):
  """Download a file from a remote source."""

  def Run(self):
    downloader = download.Download()
    for arg in self._args:
      src = arg[0]
      dst = arg[1]
      full_url = download.Transform(src, self._build_info)
      if 'https' not in full_url:  # support untagged short filenames
        full_url = download.PathCompile(self._build_info, file_name=full_url)
      try:
        file_util.CreateDirectories(dst)
      except file_util.Error as e:
        raise ActionError('Could not create destination directory %s. %s' %
                          (dst, e))
      try:
        downloader.DownloadFile(full_url, dst, show_progress=True)
      except download.DownloadError as e:
        downloader.PrintDebugInfo()
        raise ActionError('Transfer error while downloading %s: %s' %
                          (full_url, str(e)))
      if len(arg) > 2 and arg[2]:
        logging.info('Verifying SHA256 hash for %s.', dst)
        hash_ok = downloader.VerifyShaHash(dst, arg[2])
        if not hash_ok:
          raise ActionError('SHA256 hash for %s was incorrect.' % dst)

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
    except IndexError:
      raise ActionError('Unable to determine desired paths from %s.' %
                        str(self._args))

    try:
      file_util.CreateDirectories(out_path)
    except file_util.Error:
      raise ActionError('Unable to create output path %s.' % out_path)

    try:
      zf = zipfile.ZipFile(zip_file)
      zf.extractall(out_path)
    except (IOError, zipfile.BadZipfile) as e:
      raise ActionError('Bad zip file given as input.  %s' % e)

  def Validate(self):
    self._ListOfStringsValidator(self._args, 2)
