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

"""Simplify access to Glazier policy modules."""

from __future__ import absolute_import

# do not remove: internal placeholder 1
from glazier.lib.policies import base
from glazier.lib.policies import device_model
from glazier.lib.policies import disk_encryption
from glazier.lib.policies import os

# pylint: disable=invalid-name
BannedPlatform = device_model.BannedPlatform
DeviceModel = device_model.DeviceModel
DiskEncryption = disk_encryption.DiskEncryption
UnsupportedOs = os.UnsupportedOs

ImagingPolicyException = base.ImagingPolicyException
ImagingPolicyWarning = base.ImagingPolicyWarning
