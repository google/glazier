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


def RaiseFrom(*exception_chain):
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
