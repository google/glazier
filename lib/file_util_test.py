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

"""Tests for glazier.lib.file_util."""

from pyfakefs import fake_filesystem
from glazier.lib import file_util
from google.apputils import basetest


class FileUtilTest(basetest.TestCase):

  def setUp(self):
    self.filesystem = fake_filesystem.FakeFilesystem()
    file_util.os = fake_filesystem.FakeOsModule(self.filesystem)
    file_util.open = fake_filesystem.FakeFileOpen(self.filesystem)

  def testCreateDirectories(self):
    self.filesystem.CreateFile('/test')
    self.assertRaises(file_util.Error, file_util.CreateDirectories,
                      '/test/file.txt')
    file_util.CreateDirectories('/tmp/test/path/file.log')
    self.assertTrue(self.filesystem.Exists('/tmp/test/path'))
