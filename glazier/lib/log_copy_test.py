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
from unittest import mock

from absl.testing import absltest
from glazier.lib import log_copy
from glazier.lib import test_utils
from glazier.lib import winpe

from glazier.lib import constants


class LogCopyTest(test_utils.GlazierTestCase):

  @mock.patch.object(winpe, 'check_winpe', autospec=True)
  @mock.patch.object(log_copy.logging, 'FileHandler', autospec=True)
  def setUp(self, unused_handler, mock_check_winpe):
    super(LogCopyTest, self).setUp()
    mock_check_winpe.return_value = False
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
  def test_get_log_file_name(self, mock_get_value, unused_log, mock_now):
    lc = log_copy.LogCopy()
    mock_get_value.return_value = 'WORKSTATION1-W'
    now = datetime.datetime.utcnow()
    out_date = now.replace(microsecond=0).isoformat().replace(':', '')
    mock_now.return_value = now
    result = lc._GetLogFileName()
    self.assertEqual(result, r'l:\WORKSTATION1-W-' + out_date + '.log')
    mock_get_value.assert_called_with('name', path=constants.REG_ROOT)

  @mock.patch.object(log_copy.LogCopy, '_EventLogUpload', autospec=True)
  def test_event_log_copy(self, mock_eventlogupload):
    self.lc.EventLogCopy(self.log_file)
    mock_eventlogupload.assert_called_with(self.lc, self.log_file)

  @mock.patch.object(winpe, 'check_winpe', autospec=True)
  @mock.patch.object(log_copy.LogCopy, '_GetLogFileName', autospec=True)
  @mock.patch.object(log_copy.shutil, 'copy', autospec=True)
  @mock.patch.object(log_copy.drive_map.DriveMap, 'UnmapDrive', autospec=True)
  @mock.patch.object(log_copy.drive_map.DriveMap, 'MapDrive', autospec=True)
  def test_share_upload(
      self, mock_mapdrive, mock_unmapdrive, mock_copy, mock_getlogfilename,
      mock_check_winpe):

    class TestCredProvider(log_copy.LogCopyCredentials):

      def GetUsername(self):
        mock_check_winpe.return_value = False
        return 'test_user'

      def GetPassword(self):
        mock_check_winpe.return_value = False
        return 'test_pass'

    log_copy.LogCopyCredentials = TestCredProvider

    log_host = 'log-host.example.com'
    mock_getlogfilename.return_value = 'log.txt'
    self.lc.ShareCopy(self.log_file, log_host)
    mock_mapdrive.assert_called_with(
        mock.ANY, 'l:', 'log-host.example.com', 'test_user', 'test_pass')
    mock_copy.assert_called_with(self.log_file, 'log.txt')
    mock_unmapdrive.assert_called_with(mock.ANY, 'l:')

    # map error
    mock_mapdrive.return_value = None
    with self.assert_raises_with_validation(log_copy.LogCopyError):
      self.lc.ShareCopy(self.log_file, log_host)

    # copy error
    mock_mapdrive.return_value = True
    mock_copy.side_effect = shutil.Error()
    with self.assert_raises_with_validation(log_copy.LogCopyError):
      self.lc.ShareCopy(self.log_file, log_host)


if __name__ == '__main__':
  absltest.main()
