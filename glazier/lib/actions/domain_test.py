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

"""Tests for glazier.lib.actions.domain."""

from unittest import mock

from absl.testing import absltest
from absl.testing import parameterized
from glazier.lib import test_utils
from glazier.lib.actions import domain


class DomainTest(test_utils.GlazierTestCase):

  @mock.patch.object(domain.domain_join, 'DomainJoin', autospec=True)
  @mock.patch('glazier.lib.buildinfo.BuildInfo', autospec=True)
  def test_domain_join(self, mock_buildinfo, mock_domainjoin):

    args = ['interactive', 'domain.test.com']
    dj = domain.DomainJoin(args, mock_buildinfo)
    dj.Run()
    mock_domainjoin.assert_called_with('interactive', 'domain.test.com', None)

    # default ou
    args += ['OU=Test,DC=DOMAIN,DC=TEST,DC=COM']
    dj = domain.DomainJoin(args, mock_buildinfo)
    dj.Run()
    mock_domainjoin.assert_called_with(
        'interactive', 'domain.test.com', 'OU=Test,DC=DOMAIN,DC=TEST,DC=COM')

    # error
    mock_domainjoin.return_value.JoinDomain.side_effect = (
        domain.domain_join.DomainJoinError('join failed'))
    with self.assert_raises_with_validation(domain.ActionError):
      dj.Run()

  @parameterized.named_parameters(
      ('_not_a_list', 'interactive', None),
      ('_invalid_list_member_types', [1, 2, 3], None),
      ('_list_too_short', [1], None),
      ('_invalid_list_member_values', ['unknown'], None),
  )
  def test_domain_join_validation_failure(self, join_args, build_info):
    dj = domain.DomainJoin(join_args, build_info)
    with self.assert_raises_with_validation(domain.ValidationError):
      dj.Validate()

  def test_domain_join_validation_success(self):
    dj = domain.DomainJoin(['interactive', 'domain.test.com'], None)
    dj.Validate()


if __name__ == '__main__':
  absltest.main()
