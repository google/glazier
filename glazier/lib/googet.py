# python3
# Copyright 2019 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copty of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""GooGet Python Wrapper."""

import logging
import os
import re
import time
import typing
from typing import List, Optional

# do not remove: internal placeholder 1
from glazier.lib import constants
from glazier.lib import execute
from glazier.lib import winpe

if typing.TYPE_CHECKING:
  from glazier.lib import buildinfo


class Error(Exception):
  pass


class GooGetInstall(object):
  """Install an application via GooGet."""

  def _AddFlags(self,
                flags: List[str],
                branch: Optional[str] = None) -> List[str]:
    r"""Add optional flags to GooGet command.

    Short name support:
      %: A reference to the active release branch.
      \%: Escaped % character - replaced by % in string

    Args:
      flags: optional flags passed to GooGet such as urls for -sources and
        -reinstall
      branch: active release branch

    Raises:
      Error: GooGet flags(s) were not passed as a list
      Error: GooGet source(s) not specified

    Returns:
      Adjusted strings that are part of the sources array.
    """
    if not isinstance(flags, list):
      raise Error('GooGet flags were not passed as a list')

    # URL should be kept separate from other optional flags
    url, options = [], []

    if re.search(r'(-root)', str(flags)):
      raise Error('Root flag detected, remove flag to continue.')

    if re.search(r'(-sources)', str(flags)):
      raise Error('Sources keyword detected, Enter URL without \'-sources\'')

    for flag in flags:
      # Find all URLs
      if re.findall(r'http[s]?://', str(flag)):
        # If the % character was used, replace that with the build branch
        flag = re.sub(r'(?<!\\)%', str(branch), flag)

        # If the \% character was used, replace it with %
        flag = re.sub(r'\\%', '%', flag)

        url.append(flag)
      else:
        options.append(flag)

    flags = []

    if url:
      # Sources format required for the GooGet install command
      flags.append('-sources')
      flags.extend([', '.join(url)])

    if options:
      flags.extend(options)

    return flags

  def _GooGet(self) -> str:
    if winpe.check_winpe():
      return str(constants.WINPE_GOOGETROOT)
    else:
      return str(constants.SYS_GOOGETROOT)

  def LaunchGooGet(self, pkg: str, retries: int, sleep: int,
                   build_info: 'buildinfo.BuildInfo', **kwargs):
    """Launch the GooGet executable with arguments.

    Args:
      pkg: package name
      retries: number of times to retry a failed GooGet installation
      sleep: number of seconds between retry attempts
      build_info: current build information - used to get active release branch
      **kwargs: optional parameters such as path to GooGet binary, -reinstall,
      and/or -sources

    Raises:
      Error: The GooGet command failed.
    """
    if not kwargs['path']:
      kwargs['path'] = os.path.join(self._GooGet(), 'googet.exe')
    if not os.path.exists(kwargs['path']):
      raise Error('Cannot find path of GooGet binary [%s]' % kwargs['path'])
    if not pkg:
      raise Error('Missing package name for GooGet install.')

    # Pass --root as GOOGETROOT environmental variable may not exist
    root = '--root=' + self._GooGet()

    cmd = ['-noconfirm', root, 'install']

    if kwargs['flags']:
      cmd.extend(self._AddFlags(kwargs['flags'], build_info.Branch()))

    # Add the package name to the end of the command, this must be done last.
    cmd.append(pkg)

    max_attempts = retries + 1

    for i in range(1, max_attempts + 1):
      logging.info('Attempt %d of %d', i, max_attempts)

      try:
        execute.execute_binary(kwargs['path'], cmd)
        return
      except execute.Error as e:
        logging.warning(str(e))
        logging.info('Retrying in %d seconds', sleep)
        time.sleep(sleep)

    raise Error('GooGet command failed after %d attempts' % retries)
