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
"""Tests for glazier.lib.errors."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os


from absl.testing import absltest
from glazier.lib import constants
from glazier.lib import error
import mock
from pyfakefs.fake_filesystem_unittest import Patcher

_SUFFIX_WITH_CODE = (
    f'Need help? Visit {constants.HELP_URI}#1337')


class ErrorsTest(absltest.TestCase):

  def test_collect(self):
    with Patcher() as patcher:
      files = [
          os.path.join(constants.SYS_LOGS_PATH, 'log1.log'),
          os.path.join(constants.SYS_LOGS_PATH, 'log2.log'),
      ]
      patcher.fs.create_dir(constants.SYS_CACHE)
      patcher.fs.create_file(files[0], contents='log1 content')
      patcher.fs.create_file(files[1], contents='log2 content')
      error.zip_logs()
      with error.zipfile.ZipFile(
          os.path.join(constants.SYS_CACHE, 'glazier_logs.zip'),
          'r') as out:
        with out.open(files[1].lstrip('/')) as f2:
          self.assertEqual(f2.read(), b'log2 content')

  @mock.patch.object(error.zipfile.ZipFile, 'write', autospec=True)
  def test_collect_io_error(self, wr):
    wr.side_effect = IOError
    with self.assertRaises(SystemExit):
      error.zip_logs()

  @mock.patch.object(error.zipfile.ZipFile, 'write', autospec=True)
  def test_collect_value_error(self, wr):
    wr.side_effect = ValueError('ZIP does not support timestamps before 1980')
    with Patcher() as patcher:
      patcher.fs.create_dir(constants.SYS_LOGS_PATH)
      patcher.fs.create_file(os.path.join(constants.SYS_LOGS_PATH, 'log1.log'))
      with self.assertRaises(SystemExit):
        error.zip_logs()

  @mock.patch.object(error, 'zip_logs', autospec=True)
  @mock.patch.object(error.logging, 'critical', autospec=True)
  def test_glazier_error_default(self, crit, ziplogs):
    with self.assertRaises(SystemExit):
      error.GlazierError()
    self.assertTrue(crit.called)
    self.assertTrue(ziplogs.called)

  @mock.patch.object(error.logging, 'critical', autospec=True)
  def test_glazier_error_custom(self, crit):
    with self.assertRaises(SystemExit):
      error.GlazierError(1337, 'The exception', False, a='code')
    crit.assert_called_with(
        f'Reserved code\n\nException: The exception\n\n{_SUFFIX_WITH_CODE}')


if __name__ == '__main__':
  absltest.main()
