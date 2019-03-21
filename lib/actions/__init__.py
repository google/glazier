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

"""Simplify access to Glazier action modules."""

from __future__ import absolute_import

from . import abort
from . import base
from . import domain
from . import drivers
from . import file_system
from . import files
from . import installer
from . import powershell
from . import registry
from . import sysprep
from . import system
from . import timers
from . import tpm
from . import updates

# pylint: disable=invalid-name
Abort = abort.Abort
AddChoice = installer.AddChoice
BitlockerEnable = tpm.BitlockerEnable
BuildInfoDump = installer.BuildInfoDump
BuildInfoSave = installer.BuildInfoSave
CopyFile = file_system.CopyFile
DomainJoin = domain.DomainJoin
DriverWIM = drivers.DriverWIM
Execute = files.Execute
ExitWinPE = installer.ExitWinPE
Get = files.Get
LogCopy = installer.LogCopy
MkDir = file_system.MkDir
MultiCopyFile = file_system.MultiCopyFile
PSScript = powershell.PSScript
Reboot = system.Reboot
RegAdd = registry.RegAdd
MultiRegAdd = registry.MultiRegAdd
RegDel = registry.RegDel
MultiRegDel = registry.MultiRegDel
SetTimer = timers.SetTimer
SetUnattendTimeZone = sysprep.SetUnattendTimeZone
SetupCache = file_system.SetupCache
ShowChooser = installer.ShowChooser
Shutdown = system.Shutdown
Sleep = installer.Sleep
Unzip = files.Unzip
UpdateMSU = updates.UpdateMSU
Warn = abort.Warn

ActionError = base.ActionError
ValidationError = base.ValidationError

RestartEvent = base.RestartEvent
ShutdownEvent = base.ShutdownEvent

# Legacy naming
choice = installer.AddChoice
copy = file_system.MultiCopyFile
driver = drivers.DriverWIM
pull = files.Get
run = files.Execute

