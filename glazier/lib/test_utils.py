# Copyright 2022 Google Inc. All Rights Reserved.
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
"""Utility code for use with tests."""

import os
import re
from unittest import mock
from absl.testing import parameterized

from glazier.lib import errors


def raise_from(*exception_chain):
  """Collapses multiple Exceptions into a final Exception, using raise/from."""

  previous_ex = exception_chain[0]

  for current_ex in exception_chain[1:]:
    try:

      # Raise the previous exception in the chain.
      try:
        raise previous_ex

      # Catch it and wrap it in the current exception.
      except Exception as e:  # pylint: disable=broad-except
        raise current_ex from e

    except Exception as new_previous_ex:  # pylint: disable=broad-except
      previous_ex = new_previous_ex

  return previous_ex


def _exception_validation_predicate(exception):
  """Predicate for validating that raised Exceptions are properly formed.

  Args:
    exception: The Exception to validate.

  Returns:
    True if the Exception if properly formed, False otherwise.
  """
  # We shouldn't ever be raising a GlazierError subclass containing the DEFAULT
  # error code, as this likely means that we have an incomplete subclass
  # implementation somewhere.
  glazier_errors = errors.get_glazier_error_lineage(exception)
  for glazier_error in glazier_errors:
    if glazier_error.error_code == errors.ErrorCode.DEFAULT:
      return False

  return True


class GlazierTestCase(parameterized.TestCase):
  """General-purpose test case for Glazier unit tests."""

  def assert_lines_match_patterns(self, lines, patterns):
    """Asserts that each given line matches the corresponding pattern."""

    # Ensure the input is split by newlines.
    lines = lines.splitlines() if isinstance(lines, str) else lines

    # Strip out all empty lines.
    lines = list(filter(None, lines))

    # Ensure the lines and patterns match up 1:1.
    self.assertEqual(len(lines), len(patterns))

    # Step through each line and pattern and make sure they match.
    for line, pattern in zip(lines, patterns):
      regex = re.compile(pattern)
      self.assertRegex(line, regex)

  def assert_raises_with_validation(self, expected_exception):
    return self.assertRaisesWithPredicateMatch(expected_exception,
                                               _exception_validation_predicate)

  def assert_path_exists(self, file_path):
    self.assertTrue(os.path.exists(file_path))

  def assert_path_does_not_exist(self, file_path):
    self.assertFalse(os.path.exists(file_path))

  def assert_file_contents(self, file_path, contents):
    self.assert_path_exists(file_path)
    with open(file_path, 'r') as f:
      self.assertEqual(contents, f.read())

  def patch(self, target, attribute, **kwargs):
    patcher = mock.patch.object(target, attribute, **kwargs)
    self.addCleanup(patcher.stop)
    return patcher.start()

  def patch_constant(self, module, key, value):
    patcher = mock.patch.dict(module.__dict__, values={key: value})
    self.addCleanup(patcher.stop)
    return patcher.start()

  def patch_constant_file_path(self, module, key, file_name=None, content=None):
    temp_dir = self.create_tempdir()
    temp_file_path = temp_dir.create_file(
        file_path=file_name, content=content).full_path
    self.patch_constant(module, key, temp_file_path)
    return temp_file_path
