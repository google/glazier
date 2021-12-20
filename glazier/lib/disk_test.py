# Copyright 2021 Google Inc. All Rights Reserved.
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
"""Tests for glazier.lib.disk."""

import collections
import shutil
from unittest import mock

from absl.testing import absltest
from glazier.lib import disk

_SPACE = collections.namedtuple('space', 'total used free')
_DISK = _SPACE(total=1073741824000, used=536870912000, free=536870912000)


class DiskTest(absltest.TestCase):

  @mock.patch.object(shutil, 'disk_usage', autospec=True)
  def test_get_disk_space(self, usage):
    usage.return_value = _DISK
    self.assertEqual(disk.get_disk_space(), _DISK)

  @mock.patch.object(disk.logging, 'error', autospec=True)
  @mock.patch.object(shutil, 'disk_usage', autospec=True)
  def test_get_disk_space_error(self, usage, err):
    usage.side_effect = FileNotFoundError
    disk.get_disk_space()
    self.assertTrue(err.called)

  @mock.patch.object(disk.registry, 'set_value', autospec=True)
  @mock.patch.object(disk, 'get_disk_space', autospec=True)
  def test_set_disk_space(self, get_space, sv):
    get_space.return_value = _DISK
    disk.set_disk_space()
    sv.assert_has_calls([
        mock.call(
            'disk_space_total_bytes',
            mock.ANY,
            path=disk.constants.REG_ROOT),
        mock.call(
            'disk_space_used_bytes',
            mock.ANY,
            path=disk.constants.REG_ROOT),
        mock.call(
            'disk_space_free_bytes',
            mock.ANY,
            path=disk.constants.REG_ROOT)
    ])

  @mock.patch.object(disk.registry.registry, 'Registry', autospec=True)
  @mock.patch.object(disk.logging, 'error', autospec=True)
  def test_set_disk_space_error(self, err, reg):
    reg.return_value.SetKeyValue.side_effect = disk.registry.registry.RegistryError
    disk.set_disk_space()
    self.assertTrue(err.called)

if __name__ == '__main__':
  absltest.main()
