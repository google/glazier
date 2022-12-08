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
"""Tests for glazier.lib.execute."""

import io
from unittest import mock

from absl.testing import absltest
from glazier.lib import execute
from glazier.lib import test_utils

from glazier.lib import errors


class ExecuteTest(test_utils.GlazierTestCase):

  def setUp(self):
    super(ExecuteTest, self).setUp()
    self.binary = r'C:\foo.exe'

  @mock.patch.object(execute.logging, 'info', autospec=True)
  @mock.patch.object(execute.subprocess, 'Popen', autospec=True)
  def test_execute_binary(self, mock_popen, mock_info):
    popen_instance = mock_popen.return_value
    popen_instance.returncode = 0
    popen_instance.stdout = io.BytesIO(b'foo\n\n\n')
    execute.execute_binary(self.binary, ['arg1', 'arg2'])
    mock_info.assert_has_calls([
        mock.call('Executing: %s', 'C:\\foo.exe arg1 arg2'),
        mock.call(b'foo')
    ],)
    mock_popen.assert_called_with(
        [self.binary, 'arg1', 'arg2'], shell=False,
        stdout=execute.subprocess.PIPE, stderr=execute.subprocess.STDOUT,
        universal_newlines=True)

  @mock.patch.object(execute.subprocess, 'Popen', autospec=True)
  def test_execute_binary_no_args(self, mock_popen):
    popen_instance = mock_popen.return_value
    popen_instance.returncode = 0
    popen_instance.stdout = io.BytesIO(b'foo\nbar')
    execute.execute_binary(self.binary)
    mock_popen.assert_called_with(
        [self.binary], shell=False, stdout=execute.subprocess.PIPE,
        stderr=execute.subprocess.STDOUT, universal_newlines=True)

  @mock.patch.object(execute.subprocess, 'Popen', autospec=True)
  def test_execute_binary_return_codes(self, mock_popen):
    popen_instance = mock_popen.return_value
    popen_instance.returncode = 1337
    popen_instance.stdout = io.BytesIO(b'foo\nbar')
    execute.execute_binary(self.binary, return_codes=[1337, 1338])
    mock_popen.assert_called_with(
        [self.binary], shell=False, stdout=execute.subprocess.PIPE,
        stderr=execute.subprocess.STDOUT, universal_newlines=True)

  @mock.patch.object(execute.subprocess, 'Popen', autospec=True)
  def test_execute_binary_invalid_return(self, mock_popen):
    popen_instance = mock_popen.return_value
    popen_instance.returncode = 1337
    popen_instance.stdout = io.BytesIO(b'foo\nbar')
    with self.assert_raises_with_validation(execute.Error):
      execute.execute_binary(self.binary, return_codes=[1338])

  @mock.patch.object(execute.subprocess, 'Popen', autospec=True)
  def test_execute_binary_check_return(self, mock_popen):
    popen_instance = mock_popen.return_value
    popen_instance.returncode = 1337
    popen_instance.stdout = io.BytesIO(b'foo\nbar')
    self.assertEqual(
        execute.execute_binary(self.binary, check_return_code=True), 1337)

  @mock.patch.object(execute.subprocess, 'Popen', autospec=True)
  def test_execute_binary_windows_error(self, mock_popen):
    execute.WindowsError = Exception
    mock_popen.side_effect = execute.WindowsError
    with self.assert_raises_with_validation(execute.Error):
      execute.execute_binary(self.binary)

  @mock.patch.object(execute.logging, 'info', autospec=True)
  @mock.patch.object(execute.subprocess, 'Popen', autospec=True)
  def test_execute_binary_silent(self, mock_popen, mock_info):
    popen_instance = mock_popen.return_value
    popen_instance.returncode = 0
    popen_instance.stdout = io.BytesIO(b'foo\nbar')
    execute.execute_binary(self.binary, log=False)
    mock_info.assert_not_called()
    mock_popen.assert_called_with(
        [self.binary], shell=False, stdout=execute.subprocess.PIPE,
        stderr=execute.subprocess.STDOUT, universal_newlines=True)
    self.assertTrue(popen_instance.wait.called)

  @mock.patch.object(execute.logging, 'info', autospec=True)
  @mock.patch.object(execute.subprocess, 'Popen', autospec=True)
  def test_execute_binary_shell(self, mock_popen, mock_info):
    popen_instance = mock_popen.return_value
    popen_instance.returncode = 0
    popen_instance.stdout = io.BytesIO(b'foo\nbar')
    execute.execute_binary(self.binary, shell=True)
    mock_info.assert_called_with('Executing: %s', self.binary)
    mock_popen.assert_called_with(
        [self.binary], shell=True, stdout=None, stderr=None,
        universal_newlines=True)
    self.assertTrue(popen_instance.wait.called)

  @mock.patch.object(execute.logging, 'info', autospec=True)
  @mock.patch.object(execute.subprocess, 'check_output', autospec=True)
  def test_check_output(self, mock_check_output, mock_info):
    execute.check_output(self.binary, ['arg1', 'arg2'])
    mock_info.assert_called_with('Executing: %s', 'C:\\foo.exe arg1 arg2')
    mock_check_output.assert_called_with(
        [self.binary, 'arg1', 'arg2'], stderr=-2, stdin=-1, timeout=300,
        universal_newlines=True)

  @mock.patch.object(execute.logging, 'info', autospec=True)
  @mock.patch.object(execute.subprocess, 'check_output', autospec=True)
  def test_check_output_error(self, mock_check_output, mock_info):
    mock_check_output.side_effect = execute.subprocess.CalledProcessError(
        1, self.binary, b'output')
    with self.assert_raises_with_validation(execute.errors.GlazierError) as cm:
      execute.check_output(self.binary, ['arg1', 'arg2'])
    self.assertEqual(cm.exception.error_code, errors.ErrorCode.EXECUTION_RETURN)
    self.assertIsNotNone(cm.exception)
    mock_info.assert_called_with('Executing: %s', 'C:\\foo.exe arg1 arg2')

  @mock.patch.object(execute.logging, 'info', autospec=True)
  @mock.patch.object(execute.subprocess, 'check_output', autospec=True)
  def test_check_output_timeout(self, mock_check_output, mock_info):
    mock_check_output.side_effect = execute.subprocess.TimeoutExpired(
        self.binary, 300, b'output')
    with self.assert_raises_with_validation(execute.errors.GlazierError) as cm:
      execute.check_output(self.binary, ['arg1', 'arg2'])
    self.assertEqual(
        cm.exception.error_code, errors.ErrorCode.EXECUTION_TIMEOUT)
    self.assertIsNotNone(cm.exception)
    mock_info.assert_called_with('Executing: %s', 'C:\\foo.exe arg1 arg2')


if __name__ == '__main__':
  absltest.main()
