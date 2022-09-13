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

"""Tests for glazier.lib.resources."""

from unittest import mock

from absl.testing import absltest
from glazier.lib import resources
from glazier.lib import test_utils
from pyfakefs import fake_filesystem


class ResourcesTest(test_utils.GlazierTestCase):

  def setUp(self):
    super(ResourcesTest, self).setUp()
    self.fs = fake_filesystem.FakeFilesystem()
    resources.os = fake_filesystem.FakeOsModule(self.fs)
    self.fs.create_file('/test/file.txt')
    self.fs.create_file('/test2/resources/file.txt')

  def test_get_resource_file_name(self):

    r = resources.Resources('/test')
    with self.assert_raises_with_validation(resources.FileNotFound):
      r.GetResourceFileName('missing.txt')
    self.assertEqual(r.GetResourceFileName('file.txt'), '/test/file.txt')

    with mock.patch.object(resources.os.path, 'dirname') as dirname:
      dirname.return_value = '/test2'
      r = resources.Resources()
      self.assertEqual(
          r.GetResourceFileName('file.txt'), '/test2/resources/file.txt')


if __name__ == '__main__':
  absltest.main()
