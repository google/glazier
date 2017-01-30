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

"""Tests for glazier.lib.log_copy."""

import datetime
import shutil
import sys
from glazier.lib import log_copy
import mock
from google.apputils import basetest


class LogCopyTest(basetest.TestCase):

  @mock.patch.object(log_copy.logging, 'FileHandler', autospec=True)
  def setUp(self, unused_handler):
    self.log_file = r'C:\Windows\Logs\Glazier\glazier.log'
    self.lc = log_copy.LogCopy()
    # win32 modules
    self.win32netcon = mock.Mock()
    sys.modules['win32netcon'] = self.win32netcon
    self.win32wnet = mock.Mock()
    sys.modules['win32wnet'] = self.win32wnet
    self._MockWinreg()

  def _MockWinreg(self):
    winreg = mock.Mock()
    winreg.KEY_READ = 1
    winreg.KEY_WRITE = 2
    self.winreg = winreg
    sys.modules['_winreg'] = self.winreg

  def testGetLogFileName(self):
    now = datetime.datetime.utcnow()
    out_date = now.replace(microsecond=0).isoformat().replace(':', '')
    self.winreg.QueryValueEx.return_value = ['WORKSTATION1-W']
    with mock.patch.object(
        log_copy.datetime, 'datetime', autospec=True) as mock_dt:
      mock_dt.utcnow.return_value = now
      result = self.lc._GetLogFileName()
      self.assertEqual(result, r'l:\WORKSTATION1-W-' + out_date + '.log')

  @mock.patch.object(log_copy.LogCopy, '_EventLogUpload', autospec=True)
  def testEventLogCopy(self, event_up):
    self.lc.EventLogCopy(self.log_file)
    event_up.assert_called_with(self.lc, self.log_file)

  @mock.patch.object(log_copy.LogCopy, '_GetLogFileName', autospec=True)
  @mock.patch.object(log_copy.shutil, 'copy', autospec=True)
  @mock.patch.object(log_copy.drive_map.DriveMap, 'UnmapDrive', autospec=True)
  @mock.patch.object(log_copy.drive_map.DriveMap, 'MapDrive', autospec=True)
  def testShareUpload(self, map_drive, unmap_drive, copy, get_file_name):

    class TestCredProvider(log_copy.LogCopyCredentials):

      def GetUsername(self):
        return 'test_user'

      def GetPassword(self):
        return 'test_pass'

    log_copy.LogCopyCredentials = TestCredProvider

    log_host = 'log-host.example.com'
    get_file_name.return_value = 'log.txt'
    self.lc.ShareCopy(self.log_file, log_host)
    map_drive.assert_called_with(mock.ANY, 'l:', 'log-host.example.com',
                                 'test_user', 'test_pass')
    copy.assert_called_with(self.log_file, 'log.txt')
    unmap_drive.assert_called_with(mock.ANY, 'l:')
    # map error
    map_drive.return_value = None
    self.assertRaises(log_copy.LogCopyError, self.lc.ShareCopy, self.log_file,
                      log_host)
    # copy error
    map_drive.return_value = True
    copy.side_effect = shutil.Error()
    self.assertRaises(log_copy.LogCopyError, self.lc.ShareCopy, self.log_file,
                      log_host)


if __name__ == '__main__':
  basetest.main()
