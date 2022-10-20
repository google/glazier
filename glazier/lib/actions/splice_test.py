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
from unittest import mock

from absl.testing import absltest

from glazier.lib import buildinfo
from glazier.lib import splice as splice_lib
from glazier.lib import test_utils
from glazier.lib.actions import splice
from glazier.lib.actions.splice import ValidationError


class SpliceDomainJoinTest(test_utils.GlazierTestCase):

  def setUp(self):
    super(SpliceDomainJoinTest, self).setUp()
    os.environ['ProgramFiles'] = r'C:\Program Files'
    os.environ['SystemDrive'] = 'C:'

  @mock.patch.object(buildinfo, 'BuildInfo', autospec=True)
  @mock.patch.object(splice_lib.Splice, 'domain_join', autospec=True)
  def test_default(self, mock_domain_join, bi):
    self._splice = splice.SpliceDomainJoin([], bi)
    self._splice.Run()
    mock_domain_join.assert_called_with(mock.ANY, 5, True, True, '', None)

  @mock.patch.object(buildinfo, 'BuildInfo', autospec=True)
  @mock.patch.object(splice_lib.Splice, 'domain_join', autospec=True)
  def test_custom(self, mock_domain_join, mock_buildinfo):
    self._splice = splice.SpliceDomainJoin([1, False, False, 'baz'],
                                           mock_buildinfo)
    self._splice.Run()
    mock_domain_join.assert_called_with(mock.ANY, 1, False, False, 'baz', None)

  @mock.patch.object(buildinfo, 'BuildInfo', autospec=True)
  def test_cert_id_err(self, mock_buildinfo):
    self._splice = splice.SpliceDomainJoin([1, False, False, 'baz', [12345]],
                                           mock_buildinfo)
    self.assertRaises(splice.ActionError, self._splice.Run)

  @mock.patch.object(buildinfo, 'BuildInfo', autospec=True)
  @mock.patch.object(splice_lib.Splice, 'domain_join', autospec=True)
  def test_default_error(self, mock_domain_join, mock_buildinfo):
    self._splice = splice.SpliceDomainJoin([], mock_buildinfo)
    mock_domain_join.side_effect = splice_lib.Error
    self.assertRaises(splice.ActionError, self._splice.Run)

  @mock.patch.object(buildinfo, 'BuildInfo', autospec=True)
  def test_validate_retry(self, mock_buildinfo):
    self._splice = splice.SpliceDomainJoin(['a', False, False], mock_buildinfo)
    with self.assert_raises_with_validation(ValidationError):
      self._splice.Validate()

  @mock.patch.object(buildinfo, 'BuildInfo', autospec=True)
  def test_validate_unattended(self, mock_buildinfo):
    self._splice = splice.SpliceDomainJoin([5, 'paradox', False],
                                           mock_buildinfo)
    with self.assert_raises_with_validation(ValidationError):
      self._splice.Validate()

  @mock.patch.object(buildinfo, 'BuildInfo', autospec=True)
  def test_validate_fallback(self, mock_buildinfo):
    self._splice = splice.SpliceDomainJoin([5, False, 'glazier'],
                                           mock_buildinfo)
    with self.assert_raises_with_validation(ValidationError):
      self._splice.Validate()

  @mock.patch.object(buildinfo, 'BuildInfo', autospec=True)
  def test_validate_num_args(self, mock_buildinfo):
    self._splice = splice.SpliceDomainJoin([5, False, False, 'baz', 'too many'],
                                           mock_buildinfo)
    with self.assert_raises_with_validation(ValidationError):
      self._splice.Validate()


if __name__ == '__main__':
  absltest.main()
