# Copyright 2020 Google Inc. All Rights Reserved.
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
"""Levarage Splice for offline domain join."""

import logging
import os
import time

from glazier.lib import execute
from glazier.lib import identity

from glazier.lib import constants
from glazier.lib import errors


class Error(errors.GlazierError):
  pass


class IdentityError(Error):

  def __init__(self, prop: str):
    super().__init__(
        error_code=errors.ErrorCode.SPLICE_IDENTITY_ERROR,
        message=f'Error while determining {prop}')


class DomainJoinError(Error):

  def __init__(self, attempts: int):
    super().__init__(
        error_code=errors.ErrorCode.DOMAIN_JOIN_FAILURE,
        message=f'Failed to join domain after {attempts} attempt(s).')


class Splice(object):
  """Define several functions to join a machine to the domain via Splice."""

  def __init__(self):
    self.splice_binary = fr"{os.environ['ProgramFiles']}\Splice\cli.exe"
    self.splice_server = 'splice.example.com'
    self.cert_container = 'example_container'
    self.splice_generator = ''

  def _get_hostname(self) -> str:
    """Retrieve hostname from identity module.

    Returns:
      hostname of machine.
    """
    hostname = identity.get_hostname()

    if not hostname:
      try:
        hostname = identity.set_hostname()
      except identity.Error as e:
        raise IdentityError('hostname') from e

    return hostname

  def _get_username(self) -> str:
    """Retrieve username from identity module.

    Returns:
      username of desired user.
    """
    username = identity.get_username()

    if not username:
      # Clear lru_cache otherwise the next check will return no username.
      identity.get_username.cache_clear()
      try:
        username = identity.set_username(prompt='domain join')
      except identity.Error as e:
        raise IdentityError('username') from e

    return fr'{constants.DOMAIN_NAME}\{username}'

  def _splice_unattended(self):
    """Call splice binary in unattended mode."""
    args = [
        '-cert_issuer=client', f'-cert_container={self.cert_container}',
        f'-server={self.splice_server}',
        '-really_join=true', '-unattended=true'
    ]
    if self.splice_generator:
      args.append(f'-generator_id={self.splice_generator}')
    else:
      args.append(f'-name={self._get_hostname()}')

    execute.execute_binary(self.splice_binary, args, shell=True)

  def _splice_user(self):
    """Call splice binary in user auth mode."""
    args = [
        '-cert_issuer=client', f'-cert_container={self.cert_container}',
        f'-server={self.splice_server}', '-really_join=true',
        f'-user_name={self._get_username()}'
    ]
    if self.splice_generator:
      args.append(f'-generator_id={self.splice_generator}')
    else:
      args.append(f'-name={self._get_hostname()}')

    execute.execute_binary(self.splice_binary, args, shell=True)

  def domain_join(self,
                  max_retries: int = 5,
                  unattended: bool = True,
                  fallback: bool = True,
                  generator: str = ''):
    """Execute the Splice CLI with defined flags.

    Args:
      max_retries: The number of times to attempt to download a file if the
        first attempt fails. A negative number implies infinite.
      unattended: If true, execute splice in unattended mode and do not prompt
        for user credentials.
      fallback: If true and an unattended join fails, reattempt and request user
        credentials.
      generator: If specified call the splice binary with the specified hostname
        generator rather than using the current device identity.

    Raises:
      Error: Domain join failed.
    """

    attempts = 0
    sleep = 30

    self.splice_generator = generator

    while True:
      attempts += 1
      try:
        if unattended:
          self._splice_unattended()
        else:
          self._splice_user()
      except execute.Error as e:
        if max_retries < 0 or attempts < max_retries:  # pytype: disable=unsupported-operands
          logging.warning(
              'Domain join attempt %d of %d failed. Retrying in %d second(s).',
              attempts, max_retries, sleep)
          time.sleep(sleep)
        else:
          if unattended and fallback:
            logging.warning('Failed to join domain after %d attempt(s).',
                            attempts)
            logging.info(
                'Falling back to user authed domain join with %d attempts.',
                max_retries)
            break
          else:
            raise DomainJoinError(attempts) from e
      else:
        logging.info('Domain join succeeded after %d attempt(s).', attempts)
        return

    attempts = 0
    while True:
      attempts += 1
      try:
        self._splice_user()
      except execute.Error as e:
        if max_retries < 0 or attempts < max_retries:  # pytype: disable=unsupported-operands
          logging.warning(
              'Domain join attempt %d of %d failed. Retrying in %d second(s).',
              attempts, max_retries, sleep)
          time.sleep(sleep)
        else:
          raise DomainJoinError(attempts) from e
      else:
        logging.info(
            'Fallback domain join succeeded after %d attempt(s).', attempts)
        return
