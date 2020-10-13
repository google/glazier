# Lint as: python3
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
from typing import Optional, Text
from glazier.lib import execute
from glazier.lib import identity


class Error(Exception):
  pass


class Splice(object):
  """Define several functions to join a machine to the domain via Splice."""

  def __init__(self):
    self.splice_binary = r'{}\Splice\cli.exe'.format(
        os.environ['ProgramFiles'])

  def _get_hostname(self) -> Text:
    hostname = identity.get_hostname()

    if not hostname:
      try:
        hostname = identity.set_hostname()
      except identity.Error as e:
        raise Error(str(e))

    return hostname

  def _get_username(self) -> Text:
    username = identity.get_username()

    if not username:
      try:
        username = identity.set_username(prompt='domain join')
      except identity.Error as e:
        raise Error(str(e))

    return username

  def domain_join(self, max_retries: Optional[int] = 5):
    """Execute the Splice CLI with defined flags.

    Args:
      max_retries: The number of times to attempt to download a file if the
      first attempt fails. A negative number implies infinite.

    Raises:
      Error: Domain join failed.
    """
    args = [
       '-cert_issuer=client',
       '-name={}'.format(self._get_hostname()),
       '-server=splice.example.com', '-really_join=true',
       '-user_name={}'.format(self._get_username())
    ]

    attempt = 0
    sleep = 30

    while True:
      attempt += 1
      try:
        execute.execute_binary(self.splice_binary, args)
      except execute.Error:
        if max_retries < 0 or attempt < max_retries:
          logging.warning(
              'Domain join attempt %d of %d failed. Retrying in %d second(s).',
              attempt, max_retries, sleep)
          time.sleep(sleep)
        else:
          raise Error('Failed to join domain after {} attempt(s).'.format(
              max_retries))
      else:
        logging.info('Domain join succeeded after %d attempt(s).',
                     attempt)
        break
