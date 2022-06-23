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

"""This joins a Windows machine to an Active Directory domain.

Methods:
  *  auto:  Auto join the domain with no user interaction.
  *  interactive: Prompt the user for domain join credentials.
"""

import logging
import socket
import time
from glazier.lib import buildinfo
from glazier.lib import constants
from glazier.lib import interact
from glazier.lib import powershell

from glazier.lib import errors


AUTH_OPTS = [
    'auto',
    'interactive',
]


class Error(errors.GlazierError):
  pass


class DomainJoinError(Error):

  def __init__(self, message: str):
    super().__init__(
        error_code=errors.ErrorCode.DOMAIN_JOIN_FAILURE,
        message=message)


class DomainJoinCredentials(object):

  def __init__(self):
    self._username = None
    self._password = None

  def GetUsername(self):
    """Override to provide automatic join credentials."""
    return self._username

  def GetPassword(self):
    """Override to provide automatic join credentials."""
    return self._password


class DomainJoin(object):
  """Defines several functions used to join a machine to the domain."""

  def __init__(self, method, domain_name, ou=None):
    self._build_info = buildinfo.BuildInfo()
    self._domain_name = domain_name
    self._domain_ou = ou
    self._method = method
    self._password = None
    self._username = None

  def _AutomaticJoin(self):
    """Join the domain with automated credentials."""
    creds = DomainJoinCredentials()
    self._username = creds.GetUsername()
    self._password = creds.GetPassword()

    logging.info('Starting automated domain join.  Hostname: %s',
                 socket.gethostname())

    while True:
      # Set log=False to prevent leaking Domain Join credentials.
      ps = powershell.PowerShell(log=False)
      try:
        logging.debug('Attempting to join the domain %s.', self._domain_name)
        ps.RunLocal(
            r'%s\join-domain.ps1' % constants.SYS_CACHE,
            args=[self._username, self._password, self._domain_name])
      except powershell.Error as e:
        # Replace and mask password in error output.
        c = []
        error = str(e).split()
        for item in error:
          if self._password in item:
            c.append('************')
          else:
            c.append(item)
        # Display cleaned output
        logging.error(
            'Domain join failed. Sleeping 5 minutes then trying again. (%s)', c)
        time.sleep(300)
        continue
      logging.info('Joined the machine to the domain.')
      break

  def _SetUsername(self):
    self._username = interact.GetUsername()

  def _InteractiveJoin(self):
    """Join the domain with user-interactive dialog."""
    while True:
      self._SetUsername()

      ps = powershell.PowerShell()
      cmd = [
          'Add-Computer', '-DomainName', self._domain_name, '-Credential',
          self._username, '-PassThru'
      ]
      if self._domain_ou:
        cmd += ['-OUPath', f'"{self._domain_ou}"']
      try:
        logging.debug('Attempting to join the domain %s.', self._domain_name)
        ps.RunCommand(cmd)
      except powershell.Error as e:
        logging.error(
            'Domain join failed. Sleeping 5 minutes then trying again. (%s)', e)
        continue

      logging.info('Joined the machine to the domain.')
      break

  def JoinDomain(self):
    """Perform the domain join operation."""
    logging.debug('Beginning domain join process.')

    if self._method.startswith('auto'):
      self._AutomaticJoin()
    else:
      self._InteractiveJoin()
    logging.info('Domain join completed.')
