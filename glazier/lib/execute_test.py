# Lint as: python3
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
from absl.testing import absltest
from glazier.lib import execute
import mock


class ExecuteTest(absltest.TestCase):

  @mock.patch.object(execute.subprocess, 'Popen', autospec=True)
  def test_execute_binary(self, popen):
    popen_instance = popen.return_value
    popen_instance.returncode = 0
    popen_instance.stdout = io.BytesIO(b'foo\nbar')
    execute.execute_binary(r'C:\foo.exe', ['arg1', 'arg2'])
    popen.assert_called_with([r'C:\foo.exe', 'arg1', 'arg2'],
                             stdout=execute.subprocess.PIPE,
                             stderr=execute.subprocess.STDOUT,
                             universal_newlines=True)

  @mock.patch.object(execute.subprocess, 'Popen', autospec=True)
  def test_execute_binary_no_args(self, popen):
    popen_instance = popen.return_value
    popen_instance.returncode = 0
    popen_instance.stdout = io.BytesIO(b'foo\nbar')
    execute.execute_binary(r'C:\foo.exe')
    popen.assert_called_with([r'C:\foo.exe'],
                             stdout=execute.subprocess.PIPE,
                             stderr=execute.subprocess.STDOUT,
                             universal_newlines=True)

  @mock.patch.object(execute.subprocess, 'Popen', autospec=True)
  def test_execute_binary_return_codes(self, popen):
    popen_instance = popen.return_value
    popen_instance.returncode = 1337
    popen_instance.stdout = io.BytesIO(b'foo\nbar')
    execute.execute_binary(r'C:\foo.exe', return_codes=[1337, 1338])
    popen.assert_called_with([r'C:\foo.exe'],
                             stdout=execute.subprocess.PIPE,
                             stderr=execute.subprocess.STDOUT,
                             universal_newlines=True)

  @mock.patch.object(execute.subprocess, 'Popen', autospec=True)
  def test_execute_binary_invalid_return(self, popen):
    popen_instance = popen.return_value
    popen_instance.returncode = 1337
    popen_instance.stdout = io.BytesIO(b'foo\nbar')
    self.assertRaises(execute.Error, execute.execute_binary, r'C:\foo.exe',
                      return_codes=[1338])

  @mock.patch.object(execute.subprocess, 'Popen', autospec=True)
  def test_execute_binary_windows_error(self, popen):
    execute.WindowsError = Exception
    popen.side_effect = execute.WindowsError
    self.assertRaises(execute.Error, execute.execute_binary, r'C:\foo.exe')

  @mock.patch.object(execute.logging, 'info', autospec=True)
  @mock.patch.object(execute.subprocess, 'Popen', autospec=True)
  def test_execute_binary_silent(self, popen, i):
    popen_instance = popen.return_value
    popen_instance.returncode = 0
    popen_instance.stdout = io.BytesIO(b'foo\nbar')
    execute.execute_binary(r'C:\foo.exe', log=False)
    i.assert_called_with('Executing: %s', r'C:\foo.exe')
    popen.assert_called_with([r'C:\foo.exe'],
                             stdout=execute.subprocess.PIPE,
                             stderr=execute.subprocess.STDOUT,
                             universal_newlines=True)

if __name__ == '__main__':
  absltest.main()
