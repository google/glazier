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

"""Tests for glazier.lib.policies.os."""

from absl.testing import absltest
from glazier.lib import test_utils
from glazier.lib.policies import os

import mock


class OsTest(test_utils.GlazierTestCase):

  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def test_unsupported_os(self, mock_buildinfo):
    o = os.UnsupportedOs(mock_buildinfo)
    with self.assert_raises_with_validation(os.ImagingPolicyException):
      o.Verify()


if __name__ == '__main__':
  absltest.main()
