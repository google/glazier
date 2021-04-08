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

from absl.testing import absltest

from glazier.lib import constants
from glazier.lib import log_copy
from glazier.lib import winpe
import mock


class LogCopyTest(absltest.TestCase):

  @mock.patch.object(winpe, 'check_winpe', autospec=True)
  @mock.patch.object(log_copy.logging, 'FileHandler', autospec=True)
  def setUp(self, unused_handler, wpe):
    super(LogCopyTest, self).setUp()
    wpe.return_value = False
    self.log_file = r'C:\Windows\Logs\Glazier\glazier.log'
    self.lc = log_copy.LogCopy()
    # win32 modules
    self.win32netcon = mock.Mock()
    sys.modules['win32netcon'] = self.win32netcon
    self.win32wnet = mock.Mock()
    sys.modules['win32wnet'] = self.win32wnet

  @mock.patch.object(log_copy.gtime, 'now', autospec=True)
  @mock.patch.object(log_copy.logging, 'FileHandler', autospec=True)
  @mock.patch.object(log_copy.registry, 'get_value', autospec=True)
  def testGetLogFileName(self, gv, unused_log, dt):
    lc = log_copy.LogCopy()
    gv.return_value = 'WORKSTATION1-W'
    now = datetime.datetime.utcnow()
    out_date = now.replace(microsecond=0).isoformat().replace(':', '')
    dt.return_value = now
    result = lc._GetLogFileName()
    self.assertEqual(result, r'l:\WORKSTATION1-W-' + out_date + '.log')
    gv.assert_called_with('name', path=constants.REG_ROOT)

  @mock.patch.object(log_copy.registry, 'get_value', autospec=True)
  def testGetLogFileNameError(self, gv):
    gv.return_value = None
    self.assertRaises(log_copy.errors.GRegGetError, self.lc._GetLogFileName)

  @mock.patch.object(log_copy.LogCopy, '_EventLogUpload', autospec=True)
  def testEventLogCopy(self, event_up):
    self.lc.EventLogCopy(self.log_file)
    event_up.assert_called_with(self.lc, self.log_file)

  @mock.patch.object(winpe, 'check_winpe', autospec=True)
  @mock.patch.object(log_copy.LogCopy, '_GetLogFileName', autospec=True)
  @mock.patch.object(log_copy.shutil, 'copy', autospec=True)
  @mock.patch.object(log_copy.drive_map.DriveMap, 'UnmapDrive', autospec=True)
  @mock.patch.object(log_copy.drive_map.DriveMap, 'MapDrive', autospec=True)
  def testShareUpload(self, map_drive, unmap_drive, copy, get_file_name, wpe):

    class TestCredProvider(log_copy.LogCopyCredentials):

      def GetUsername(self):
        wpe.return_value = False
        return 'test_user'

      def GetPassword(self):
        wpe.return_value = False
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
  absltest.main()
