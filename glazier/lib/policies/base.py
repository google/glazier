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

"""Generic imaging policy class."""

from glazier.lib import errors


class ImagingPolicyException(errors.GlazierError):
  """Policy verification failed with a fatal condition."""

  def __init__(self, message: str):
    super().__init__(
        error_code=errors.ErrorCode.POLICY_VERIFICATION_ERROR,
        message=message)


class BasePolicy(object):

  def __init__(self, build_info):
    self._build_info = build_info

  def Verify(self):
    """Override this function to implement a new policy."""
    pass
