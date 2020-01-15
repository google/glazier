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

from absl.testing import absltest
from glazier.lib import logs
import mock


class LoggingTest(absltest.TestCase):

  @mock.patch.object(logs.winpe, 'check_winpe', autospec=True)
  def testGetLogsPath(self, wpe):
    # WinPE
    wpe.return_value = True
    self.assertEqual(logs.GetLogsPath(), logs.constants.WINPE_LOGS_PATH)

    # Host
    wpe.return_value = False
    self.assertEqual(logs.GetLogsPath(), logs.constants.SYS_LOGS_PATH)

  @mock.patch.object(logs.winpe, 'check_winpe', autospec=True)
  @mock.patch.object(logs.logging, 'FileHandler')
  def testSetup(self, fh, wpe):
    wpe.return_value = False
    logs.Setup()
    fh.assert_called_with('%s\\glazier.log' % logs.constants.SYS_LOGS_PATH)
    fh.side_effect = IOError
    self.assertRaises(logs.LogError, logs.Setup)


if __name__ == '__main__':
  absltest.main()
