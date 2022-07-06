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
"""Tests for glazier.lib.logs."""

import os
from unittest import mock
import zipfile

from absl.testing import absltest
from glazier.lib import constants
from glazier.lib import file_util
from glazier.lib import logs
from glazier.lib import winpe

from pyfakefs.fake_filesystem_unittest import Patcher

TEST_ID = '1A19SEL90000R90DZN7A-1234567'


class LoggingTest(absltest.TestCase):

  @mock.patch.object(winpe, 'check_winpe', autospec=True)
  def test_collect(self, mock_check_winpe):
    mock_check_winpe.return_value = False
    with Patcher() as patcher:
      files = [
          os.path.join(constants.SYS_LOGS_PATH, 'log1.log'),
          os.path.join(constants.SYS_LOGS_PATH, 'log2.log'),
      ]
      patcher.fs.create_dir(constants.SYS_LOGS_PATH)
      patcher.fs.create_file(files[0], contents='log1 content')
      patcher.fs.create_file(files[1], contents='log2 content')
      logs.Collect(r'C:\glazier.zip')
      with zipfile.ZipFile(r'C:\glazier.zip', 'r') as out:
        with out.open(files[1].lstrip('/')) as f2:
          self.assertEqual(f2.read(), b'log2 content')

  def test_collect_io_err(self):
    with Patcher() as patcher:
      patcher.fs.create_dir(constants.SYS_LOGS_PATH)
      with self.assertRaises(logs.LogCollectionError):
        logs.Collect(constants.SYS_LOGS_PATH)

  @mock.patch.object(zipfile.ZipFile, 'write', autospec=True)
  @mock.patch.object(winpe, 'check_winpe', autospec=True)
  def test_collect_value_err(self, mock_check_winpe, mock_write):
    mock_check_winpe.return_value = False
    mock_write.side_effect = ValueError(
        'ZIP does not support timestamps before 1980')
    with Patcher() as patcher:
      patcher.fs.create_dir(constants.SYS_LOGS_PATH)
      patcher.fs.create_file(os.path.join(constants.SYS_LOGS_PATH, 'log1.log'))
      with self.assertRaises(logs.LogCollectionError):
        logs.Collect(r'C:\glazier.zip')

  @mock.patch.object(winpe, 'check_winpe', autospec=True)
  def test_get_logs_path(self, mock_check_winpe):

    # WinPE
    mock_check_winpe.return_value = True
    self.assertEqual(logs.GetLogsPath(), logs.constants.WINPE_LOGS_PATH)

    # Host
    mock_check_winpe.return_value = False
    self.assertEqual(logs.GetLogsPath(), logs.constants.SYS_LOGS_PATH)

  @mock.patch.object(file_util, 'CreateDirectories')
  @mock.patch.object(logs.buildinfo.BuildInfo, 'ImageID', autospec=True)
  @mock.patch.object(winpe, 'check_winpe', autospec=True)
  @mock.patch.object(logs.logging, 'FileHandler')
  def test_setup(
      self, mock_filehandler, mock_check_winpe, mock_imageid,
      mock_createdirectories):
    mock_imageid.return_value = TEST_ID
    mock_check_winpe.return_value = False
    logs.Setup()
    mock_createdirectories.assert_called_with(
        r'%s\glazier.log' % logs.constants.SYS_LOGS_PATH)
    mock_filehandler.assert_called_with(
        r'%s\glazier.log' % logs.constants.SYS_LOGS_PATH)

  @mock.patch.object(file_util, 'CreateDirectories')
  @mock.patch.object(logs.buildinfo.BuildInfo, 'ImageID', autospec=True)
  @mock.patch.object(winpe, 'check_winpe', autospec=True)
  @mock.patch.object(logs.logging, 'FileHandler')
  def test_setup_error(
      self, mock_filehandler, mock_check_winpe, mock_imageid,
      mock_createdirectories):
    mock_imageid.return_value = TEST_ID
    mock_check_winpe.return_value = False
    mock_filehandler.side_effect = IOError
    with self.assertRaises(logs.LogOpenError):
      logs.Setup()
    self.assertTrue(mock_createdirectories.called)


if __name__ == '__main__':
  absltest.main()
