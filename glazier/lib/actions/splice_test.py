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

"""Tests for glazier.lib.actions.splice."""

import os
from absl.testing import absltest
from glazier.lib.actions import splice
import mock


class SpliceDomainJoinTest(absltest.TestCase):

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def setUp(self, bi):
    super(SpliceDomainJoinTest, self).setUp()
    os.environ['ProgramFiles'] = r'C:\Program Files'
    os.environ['SystemDrive'] = 'C:'
    self._splice = splice.SpliceDomainJoin(self, bi)

  @mock.patch.object(splice.splice.Splice, 'domain_join', autospec=True)
  def test_run(self, dj):
    self._splice.Run()
    self.assertTrue(dj.called)

  @mock.patch.object(splice.splice.Splice, 'domain_join', autospec=True)
  def test_run_error(self, dj):
    dj.side_effect = splice.splice.Error
    self.assertRaises(splice.ActionError, self._splice.Run)

if __name__ == '__main__':
  absltest.main()
