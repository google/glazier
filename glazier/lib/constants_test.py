# Copyright 2026 Google LLC
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

import os

from absl.testing import absltest
from glazier.lib import constants


class ConstantsTest(absltest.TestCase):

  def test_sys_seed_file_under_sys_cache(self):
    # The constants are built with os.path, so compare with os.path too. A
    # relative path rejects sibling directories that share the SYS_CACHE prefix.
    self.assertEqual(
        os.path.relpath(constants.SYS_SEED_FILE, constants.SYS_CACHE),
        os.path.join('resources', 'seed.json'),
    )


if __name__ == '__main__':
  absltest.main()
