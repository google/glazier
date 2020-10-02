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
import zipfile

from absl.testing import absltest
from glazier.lib import constants
from glazier.lib import logs

import mock
from pyfakefs.fake_filesystem_unittest import Patcher

TEST_ID = '1A19SEL90000R90DZN7A-1234567'


class LoggingTest(absltest.TestCase):

  def testCollect(self):
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
        with out.open(files[1]) as f2:
          self.assertEqual(f2.read(), b'log2 content')

  def testCollectIOErr(self):
    with Patcher() as patcher:
      patcher.fs.create_dir(constants.SYS_LOGS_PATH)
      with self.assertRaises(logs.LogError):
        logs.Collect(constants.SYS_LOGS_PATH)

  @mock.patch.object(zipfile.ZipFile, 'write', autospec=True)
  def testCollectValueErr(self, wr):
    wr.side_effect = ValueError('ZIP does not support timestamps before 1980')
    with Patcher() as patcher:
      patcher.fs.create_dir(constants.SYS_LOGS_PATH)
      patcher.fs.create_file(os.path.join(constants.SYS_LOGS_PATH, 'log1.log'))
      with self.assertRaises(logs.LogError):
        logs.Collect(r'C:\glazier.zip')

  @mock.patch.object(logs.winpe, 'check_winpe', autospec=True)
  def testGetLogsPath(self, wpe):
    # WinPE
    wpe.return_value = True
    self.assertEqual(logs.GetLogsPath(), logs.constants.WINPE_LOGS_PATH)

    # Host
    wpe.return_value = False
    self.assertEqual(logs.GetLogsPath(), logs.constants.SYS_LOGS_PATH)

  @mock.patch.object(logs.buildinfo.BuildInfo, 'ImageID', autospec=True)
  @mock.patch.object(logs.winpe, 'check_winpe', autospec=True)
  @mock.patch.object(logs.logging, 'FileHandler')
  def testSetup(self, fh, wpe, ii):
    ii.return_value = TEST_ID
    wpe.return_value = False
    logs.Setup()
    fh.assert_called_with(r'%s\glazier.log' % logs.constants.SYS_LOGS_PATH)

  @mock.patch.object(logs.buildinfo.BuildInfo, 'ImageID', autospec=True)
  @mock.patch.object(logs.winpe, 'check_winpe', autospec=True)
  @mock.patch.object(logs.logging, 'FileHandler')
  def testSetupError(self, fh, wpe, ii):
    ii.return_value = TEST_ID
    wpe.return_value = False
    fh.side_effect = IOError
    self.assertRaises(logs.LogError, logs.Setup)


if __name__ == '__main__':
  absltest.main()
