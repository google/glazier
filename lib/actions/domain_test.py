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

from glazier.lib.actions import domain
import mock
from google.apputils import basetest


class DomainTest(basetest.TestCase):

  @mock.patch.object(domain.domain_join, 'DomainJoin', autospec=True)
  @mock.patch(
      'glazier.lib.buildinfo.BuildInfo', autospec=True)
  def testDomainJoin(self, build_info, join):
    args = ['interactive', 'domain.test.com']
    dj = domain.DomainJoin(args, build_info)
    dj.Run()
    join.assert_called_with('interactive', 'domain.test.com', None)
    # default ou
    args += ['OU=Test,DC=DOMAIN,DC=TEST,DC=COM']
    dj = domain.DomainJoin(args, build_info)
    dj.Run()
    join.assert_called_with('interactive', 'domain.test.com',
                            'OU=Test,DC=DOMAIN,DC=TEST,DC=COM')
    # error
    join.return_value.JoinDomain.side_effect = (
        domain.domain_join.DomainJoinError)
    self.assertRaises(domain.ActionError, dj.Run)

  def testDomainJoinValidate(self):
    dj = domain.DomainJoin('interactive', None)
    self.assertRaises(domain.ValidationError, dj.Validate)
    dj = domain.DomainJoin([1, 2, 3], None)
    self.assertRaises(domain.ValidationError, dj.Validate)
    dj = domain.DomainJoin([1], None)
    self.assertRaises(domain.ValidationError, dj.Validate)
    dj = domain.DomainJoin(['unknown'], None)
    self.assertRaises(domain.ValidationError, dj.Validate)
    dj = domain.DomainJoin(['interactive', 'domain.test.com'], None)
    dj.Validate()


if __name__ == '__main__':
  basetest.main()
