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
from pyfakefs import fake_filesystem

from glazier.lib import errors


class ExecuteTest(absltest.TestCase):

  def setUp(self):
    super(ExecuteTest, self).setUp()
    self.fs = fake_filesystem.FakeFilesystem()
    execute.os = fake_filesystem.FakeOsModule(self.fs)
    execute.open = fake_filesystem.FakeFileOpen(self.fs)
    self.binary = r'C:\foo.exe'
    self.fs.create_file(self.binary)

  @mock.patch.object(execute.logging, 'info', autospec=True)
  @mock.patch.object(execute.subprocess, 'Popen', autospec=True)
  def test_execute_binary(self, popen, i):
    popen_instance = popen.return_value
    popen_instance.returncode = 0
    popen_instance.stdout = io.BytesIO(b'foo\n\n\n')
    execute.execute_binary(self.binary, ['arg1', 'arg2'])
    i.assert_has_calls([
        mock.call('Executing: %s', 'C:\\foo.exe arg1 arg2'),
        mock.call(b'foo')
    ],)
    popen.assert_called_with([self.binary, 'arg1', 'arg2'],
                             shell=False,
                             stdout=execute.subprocess.PIPE,
                             stderr=execute.subprocess.STDOUT,
                             universal_newlines=True)

  @mock.patch.object(execute.subprocess, 'Popen', autospec=True)
  def test_execute_binary_no_args(self, popen):
    popen_instance = popen.return_value
    popen_instance.returncode = 0
    popen_instance.stdout = io.BytesIO(b'foo\nbar')
    execute.execute_binary(self.binary)
    popen.assert_called_with([self.binary],
                             shell=False,
                             stdout=execute.subprocess.PIPE,
                             stderr=execute.subprocess.STDOUT,
                             universal_newlines=True)

  @mock.patch.object(execute.subprocess, 'Popen', autospec=True)
  def test_execute_binary_return_codes(self, popen):
    popen_instance = popen.return_value
    popen_instance.returncode = 1337
    popen_instance.stdout = io.BytesIO(b'foo\nbar')
    execute.execute_binary(self.binary, return_codes=[1337, 1338])
    popen.assert_called_with([self.binary],
                             shell=False,
                             stdout=execute.subprocess.PIPE,
                             stderr=execute.subprocess.STDOUT,
                             universal_newlines=True)

  @mock.patch.object(execute.subprocess, 'Popen', autospec=True)
  def test_execute_binary_invalid_return(self, popen):
    popen_instance = popen.return_value
    popen_instance.returncode = 1337
    popen_instance.stdout = io.BytesIO(b'foo\nbar')
    self.assertRaises(
        errors.BinaryExecutionError, execute.execute_binary, self.binary,
        return_codes=[1338])

  @mock.patch.object(execute.subprocess, 'Popen', autospec=True)
  def test_execute_binary_windows_error(self, popen):
    execute.WindowsError = Exception
    popen.side_effect = execute.WindowsError
    self.assertRaises(
        errors.BinaryExecutionError, execute.execute_binary, self.binary)

  @mock.patch.object(execute.logging, 'info', autospec=True)
  @mock.patch.object(execute.subprocess, 'Popen', autospec=True)
  def test_execute_binary_silent(self, popen, i):
    popen_instance = popen.return_value
    popen_instance.returncode = 0
    popen_instance.stdout = io.BytesIO(b'foo\nbar')
    execute.execute_binary(self.binary, log=False)
    i.assert_not_called()
    popen.assert_called_with([self.binary],
                             shell=False,
                             stdout=execute.subprocess.PIPE,
                             stderr=execute.subprocess.STDOUT,
                             universal_newlines=True)
    self.assertTrue(popen_instance.wait.called)

  @mock.patch.object(execute.logging, 'info', autospec=True)
  @mock.patch.object(execute.subprocess, 'Popen', autospec=True)
  def test_execute_binary_shell(self, popen, i):
    popen_instance = popen.return_value
    popen_instance.returncode = 0
    popen_instance.stdout = io.BytesIO(b'foo\nbar')
    execute.execute_binary(self.binary, shell=True)
    i.assert_called_with('Executing: %s', self.binary)
    popen.assert_called_with([self.binary],
                             shell=True,
                             stdout=None,
                             stderr=None,
                             universal_newlines=True)
    self.assertTrue(popen_instance.wait.called)

  @mock.patch.object(execute.logging, 'info', autospec=True)
  @mock.patch.object(execute.subprocess, 'check_output', autospec=True)
  def test_check_output(self, check, i):
    execute.check_output(self.binary, ['arg1', 'arg2'])
    i.assert_called_with('Executing: %s', 'C:\\foo.exe arg1 arg2')
    check.assert_called_with([self.binary, 'arg1', 'arg2'],
                             stderr=-2,
                             stdin=-1,
                             timeout=300,
                             universal_newlines=True)

  @mock.patch.object(execute.logging, 'info', autospec=True)
  @mock.patch.object(execute.subprocess, 'check_output', autospec=True)
  def test_check_output_error(self, check, i):
    check.side_effect = execute.subprocess.CalledProcessError(
        1, self.binary, b'output')
    with self.assertRaises(execute.errors.GlazierError) as cm:
      execute.check_output(self.binary, ['arg1', 'arg2'])
    self.assertEqual(cm.exception.error_code, 7006)
    self.assertIsNotNone(cm.exception)
    i.assert_called_with('Executing: %s', 'C:\\foo.exe arg1 arg2')

  @mock.patch.object(execute.logging, 'info', autospec=True)
  @mock.patch.object(execute.subprocess, 'check_output', autospec=True)
  def test_check_output_timeout(self, check, i):
    check.side_effect = execute.subprocess.TimeoutExpired(
        self.binary, 300, b'output')
    with self.assertRaises(execute.errors.GlazierError) as cm:
      execute.check_output(self.binary, ['arg1', 'arg2'])
    self.assertEqual(cm.exception.error_code, 7004)
    self.assertIsNotNone(cm.exception)
    i.assert_called_with('Executing: %s', 'C:\\foo.exe arg1 arg2')


if __name__ == '__main__':
  absltest.main()
