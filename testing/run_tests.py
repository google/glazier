# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Locate *_test modules and run the tests in them."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import pkgutil
import re
import subprocess
import sys

import glazier

FAILED_RE = re.compile(r'FAILED\s*\(errors=(\d*)\)')


def main():
  results = {'codes': {0: 0, 1: 0}, 'errors': 0}
  for _, test, _ in pkgutil.walk_packages(glazier.__path__,
                                          glazier.__name__ + '.'):
    if '_test' in test:
      print('**** %s ****\n' % test)
      proc = subprocess.Popen(['python', '-m', test], stderr=subprocess.PIPE)
      _, err = proc.communicate()
      err = err.decode()
      print(err)
      failed = FAILED_RE.search(err)
      if failed:
        results['errors'] += int(failed.group(1))
      results['codes'][proc.returncode] = results['codes'].setdefault(
          proc.returncode, 0) + 1

  print('Success: %s' % results['codes'][0])
  print('Failure: %s' % results['codes'][1])
  sys.exit(results['codes'][1])


if __name__ == '__main__':
  main()
