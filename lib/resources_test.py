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

from pyfakefs import fake_filesystem
from glazier.lib import resources
import mock
from google.apputils import basetest


class ResourcesTest(basetest.TestCase):

  def setUp(self):
    self.fs = fake_filesystem.FakeFilesystem()
    resources.os = fake_filesystem.FakeOsModule(self.fs)
    self.fs.CreateFile('/test/file.txt')
    self.fs.CreateFile('/test2/resources/file.txt')

  def testGetResourceFileName(self):
    r = resources.Resources('/test')
    self.assertRaises(resources.FileNotFound, r.GetResourceFileName,
                      'missing.txt')
    self.assertEqual(r.GetResourceFileName('file.txt'), '/test/file.txt')

    with mock.patch.object(resources.os.path, 'dirname') as dirname:
      dirname.return_value = '/test2'
      r = resources.Resources()
      self.assertEqual(
          r.GetResourceFileName('file.txt'), '/test2/resources/file.txt')


if __name__ == '__main__':
  basetest.main()
