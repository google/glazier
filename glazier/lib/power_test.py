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

"""Tests for glazier.lib.power."""

from unittest import mock

from absl.testing import absltest
from glazier.lib import constants
from glazier.lib import execute
from glazier.lib import power


class PowerTest(absltest.TestCase):

  @mock.patch.object(power.winpe, 'check_winpe', autospec=True)
  @mock.patch.object(execute, 'execute_binary', autospec=True)
  def test_restart(self, mock_execute_binary, mock_check_winpe):
    # Use WinPE paths
    mock_check_winpe.return_value = True

    power.Restart(60, 'Reboot fixes everything.')
    mock_execute_binary.assert_called_with(
        f'{constants.WINPE_SYSTEM32}/shutdown.exe',
        ['-r', '-t', '60', '-c', '"Reboot fixes everything."'])

    # Use hosts paths
    mock_check_winpe.return_value = False

    power.Restart(60, 'Reboot fixes everything.')
    mock_execute_binary.assert_called_with(
        f'{constants.SYS_SYSTEM32}/shutdown.exe',
        ['-r', '-t', '60', '-c', '"Reboot fixes everything."'])

  @mock.patch.object(power.winpe, 'check_winpe', autospec=True)
  @mock.patch.object(execute, 'execute_binary', autospec=True)
  def test_shutdown(self, mock_execute_binary, mock_check_winpe):
    # Use WinPE paths
    mock_check_winpe.return_value = True

    power.Shutdown(30, 'Because I said so.')
    mock_execute_binary.assert_called_with(
        f'{constants.WINPE_SYSTEM32}/shutdown.exe',
        ['-s', '-t', '30', '-c', '"Because I said so."'])

    # Use hosts paths
    mock_check_winpe.return_value = False

    power.Shutdown(30, 'Because I said so.')
    mock_execute_binary.assert_called_with(
        f'{constants.SYS_SYSTEM32}/shutdown.exe',
        ['-s', '-t', '30', '-c', '"Because I said so."'])

if __name__ == '__main__':
  absltest.main()
