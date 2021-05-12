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


from absl.testing import absltest
from glazier.lib import errors


class ErrorsTest(absltest.TestCase):

  def test_glazier_reserved_error_replacements(self):
    self.assertEqual(
        str(errors.GReservedError('exception', [1, 2, 3])),
        'Reserved 1 2 3 (1337): exception')

  def test_glazier_reserved_error_no_replacements(self):
    self.assertEqual(
        str(errors.GUncaughtError('exception')),
        'Uncaught exception (4000): exception')

  def test_glazier_error_str(self):
    self.assertEqual(
        str(errors.GlazierError('exception')),
        'Unknown Exception (4000): exception')


if __name__ == '__main__':
  absltest.main()
