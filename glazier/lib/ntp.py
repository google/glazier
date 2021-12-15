# python3
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

"""Glazier interface to NTP time service."""

import logging
import os
import socket
import subprocess
import time

# do not remove: internal placeholder 1

from glazier.lib.constants import WINPE_SYSTEM32
import ntplib

RETRY_DELAY = 30


class NtpException(Exception):
  pass


def SyncClockToNtp(retries: int = 2, server: str = 'time.google.com'):
  """Syncs the hardware clock to an NTP server."""
  logging.info('Reading time from NTP server %s.', server)

  attempts = 0
  client = ntplib.NTPClient()
  response = None

  while True:
    try:
      response = client.request(server, version=3)
    except (ntplib.NTPException, socket.gaierror) as e:
      logging.error('NTP client request error: %s', str(e))
    if response or attempts >= retries:
      break
    logging.info(
        'Unable to contact NTP server %s to sync machine clock.  This '
        'machine may not have an IP address yet; waiting %d seconds and '
        'trying again. Repeated failure may indicate network or driver '
        'problems.', server, RETRY_DELAY)
    time.sleep(RETRY_DELAY)
    attempts += 1

  if not response:
    raise NtpException('No response from NTP server.')

  local_time = time.localtime(response.ref_time)
  current_date = time.strftime('%m-%d-%Y', local_time)
  current_time = time.strftime('%H:%M:%S', local_time)
  logging.info('Current date/time is %s %s', current_date, current_time)

  date_set = r'%s /c date %s' % (os.path.join(WINPE_SYSTEM32,
                                              'cmd.exe'), current_date)
  result = subprocess.call(date_set, shell=True)
  logging.info('Setting date returned result %s', result)
  time_set = r'%s /c time %s' % (os.path.join(WINPE_SYSTEM32,
                                              'cmd.exe'), current_time)
  result = subprocess.call(time_set, shell=True)
  logging.info('Setting time returned result %s', result)
