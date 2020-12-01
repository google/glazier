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


from absl.testing import absltest
from glazier.lib import error
import mock
from pyfakefs import fake_filesystem

_SUFFIX_WITH_CODE = (
    f'Need help? Visit {error.constants.HELP_URI}#1337')


class ErrorsTest(absltest.TestCase):

  def setUp(self):
    super(ErrorsTest, self).setUp()
    self.fs = fake_filesystem.FakeFilesystem()
    fake_filesystem.FakeOsModule(self.fs)
    fake_filesystem.FakeFileOpen(self.fs)
    self.fs.create_file(
        error.os.path.join(error.build_info.CachePath() + error.os.sep,
                           'glazier_logs.zip'))

  @mock.patch.object(error.logs, 'Collect', autospec=True)
  def test_collect(self, collect):
    error._collect()
    self.assertTrue(collect.called)

  @mock.patch.object(error.logs, 'Collect', autospec=True)
  def test_collect_failure(self, collect):
    collect.side_effect = error.logs.LogError('something went wrong')
    with self.assertRaises(SystemExit):
      error._collect()

  @mock.patch.object(error, '_collect', autospec=True)
  @mock.patch.object(error.logging, 'critical', autospec=True)
  def test_glazier_error_default(self, crit, collect):
    with self.assertRaises(SystemExit):
      error.GlazierError()
    self.assertTrue(crit.called)
    self.assertTrue(collect.called)

  @mock.patch.object(error.logs, 'Collect', autospec=True)
  @mock.patch.object(error.logging, 'critical', autospec=True)
  def test_glazier_error_custom(self, crit, collect):
    collect.return_value = 0
    with self.assertRaises(SystemExit):
      error.GlazierError(1337, 'The exception', False, a='code')
    crit.assert_called_with(
        f'Reserved code\n\nException: The exception\n\n{_SUFFIX_WITH_CODE}')


if __name__ == '__main__':
  absltest.main()
