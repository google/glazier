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

"""Tests for glazier.lib.ntp."""

import os
import time
from glazier.lib import ntp
import mock
from google.apputils import basetest


class NtpTest(basetest.TestCase):

  @mock.patch.object(ntp.time, 'sleep', autospec=True)
  @mock.patch.object(ntp.subprocess, 'call', autospec=True)
  @mock.patch.object(ntp.ntplib.NTPClient, 'request', autospec=True)
  def testSyncClockToNtp(self, request, subproc, sleep):
    os.environ['TZ'] = 'UTC'
    time.tzset()
    return_time = mock.Mock()
    return_time.ref_time = 1453220630.64458
    request.side_effect = iter([None, None, None, return_time])
    subproc.return_value = True
    # Too Few Retries
    self.assertRaises(ntp.NtpException, ntp.SyncClockToNtp)
    sleep.assert_has_calls([mock.call(30), mock.call(30)])
    # Sufficient Retries
    ntp.SyncClockToNtp(retries=3, server='time.google.com')
    request.assert_called_with(mock.ANY, 'time.google.com', version=3)
    subproc.assert_has_calls([
        mock.call(
            r'X:\Windows\System32\cmd.exe /c date 01-19-2016', shell=True),
        mock.call(r'X:\Windows\System32\cmd.exe /c time 16:23:50', shell=True)
    ])
    # Socket Error
    request.side_effect = ntp.socket.gaierror
    self.assertRaises(ntp.NtpException, ntp.SyncClockToNtp)
    # NTP lib error
    request.side_effect = ntp.ntplib.NTPException
    self.assertRaises(ntp.NtpException, ntp.SyncClockToNtp)


if __name__ == '__main__':
  basetest.main()
