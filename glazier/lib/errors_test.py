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
"""Tests for glazier.lib.errors."""

import inspect
import random
import string

from absl.testing import absltest
from absl.testing import parameterized
from glazier.lib import errors
from glazier.lib import test_utils

ErrorCode = errors.ErrorCode


class GlazierErrorTest(parameterized.TestCase):

  @parameterized.named_parameters(
      (
          '_NoInitArgs',
          None, None, None,
          'Unknown Exception (Error Code: 7000)'
      ),
      (
          '_ErrorCodeOnly',
          9999, None, None,
          'Unknown Exception (Error Code: 9999)'
      ),
      (
          '_MessageOnly',
          None, 'some error message', None,
          'some error message (Error Code: 7000)'
      ),
      (
          '_ErrorCodeAndMessage',
          9999, 'some error message', None,
          'some error message (Error Code: 9999)'
      ),
      (
          '_NoInitArgs_WithCause',
          None, None, [Exception('inner message')],
          'Unknown Exception (Error Code: 7000) (Cause: inner message)'
      ),
      (
          '_ErrorCodeOnly_WithCause',
          9999, None, [Exception('inner message')],
          'Unknown Exception (Error Code: 9999) (Cause: inner message)'
      ),
      (
          '_MessageOnly_WithCause',
          None, 'some error message', [Exception('inner message')],
          'some error message (Error Code: 7000) (Cause: inner message)'
      ),
      (
          '_ErrorCodeAndMessage_WithCause',
          9999, 'some error message', [Exception('inner message')],
          'some error message (Error Code: 9999) (Cause: inner message)'
      ),
      (
          '_MultipleRaisesFrom',
          9999, 'outer message',
          [
              errors.GlazierError(error_code=1111, message='inner message 1'),
              errors.GlazierError(error_code=2222, message='inner message 2'),
          ],
          'outer message (Error Code: 9999) (Cause: inner message 2)'
      ),
  )
  def test_str(self, error_code, message, exception_chain, expected_str):

    err = errors.GlazierError(error_code=error_code, message=message)
    if exception_chain:
      err = test_utils.raise_from(*exception_chain, err)

    self.assertEqual(expected_str, str(err))

  def test_subclasses(self):

    def predicate(m):
      return inspect.isclass(m) and m != errors.GlazierError and m != ErrorCode

    # Collect all subclasses of GlazierError in the "errors" module.
    tuples = inspect.getmembers(errors, predicate)
    subclasses = [t[1] for t in tuples]

    # Track the encountered error codes, in order to detect duplicates.
    encountered_error_codes = set([])

    # For each GlazierError subclass, use inspection to figure out all the
    # positional arguments.
    for subclass in subclasses:

      init_args = []

      # Inspect the __init__ method, which returns a dict of
      # (str, inspect.Parameter) pairs.
      init_params = inspect.signature(subclass.__init__).parameters
      for param_name, param_obj in init_params.items():

        # Just skip the 'self' arg.
        if param_name == 'self':
          continue

        # Try to intelligently create a dummy value for the arg based on the
        # type annotation. If there isn't one, just default to str.
        if param_obj.annotation == int:
          init_args.append(random.randint(0, 100))
        elif param_obj.annotation == float:
          init_args.append(random.random() * 10)
        else:
          random_str = ''.join(random.sample(string.ascii_lowercase, 8))
          init_args.append(random_str)

      # Verify that the given subclass can be constructed without issue, using
      # the randomly generated args. This should catch any name mismatches or
      # size discrepancies between the constructor args, and the inner message
      # format string.
      err_obj = subclass(*init_args)

      # If this error has a duplicate error code, bail.
      self.assertNotIn(err_obj.error_code, encountered_error_codes)
      encountered_error_codes.add(err_obj.error_code)


if __name__ == '__main__':
  absltest.main()
