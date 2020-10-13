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


from glazier.lib.actions import abort
from glazier.lib.actions import base
from glazier.lib.actions import domain
from glazier.lib.actions import drivers
from glazier.lib.actions import file_system
from glazier.lib.actions import files
from glazier.lib.actions import googet
from glazier.lib.actions import installer
from glazier.lib.actions import powershell
from glazier.lib.actions import registry
from glazier.lib.actions import splice
from glazier.lib.actions import sysprep
from glazier.lib.actions import system
from glazier.lib.actions import timers
from glazier.lib.actions import tpm
from glazier.lib.actions import updates

# pylint: disable=invalid-name
Abort = abort.Abort
AddChoice = installer.AddChoice
BitlockerEnable = tpm.BitlockerEnable
BuildInfoDump = installer.BuildInfoDump
BuildInfoSave = installer.BuildInfoSave
ChangeServer = installer.ChangeServer
CopyDir = file_system.CopyDir
CopyFile = file_system.CopyFile
DomainJoin = domain.DomainJoin
DriverWIM = drivers.DriverWIM
Execute = files.Execute
ExitWinPE = installer.ExitWinPE
Get = files.Get
GooGetInstall = googet.GooGetInstall
LogCopy = installer.LogCopy
MkDir = file_system.MkDir
MultiCopyFile = file_system.MultiCopyFile
PSScript = powershell.PSScript
MultiPSScript = powershell.MultiPSScript
PSCommand = powershell.PSCommand
MultiPSCommand = powershell.MultiPSCommand
Reboot = system.Reboot
RegAdd = registry.RegAdd
MultiRegAdd = registry.MultiRegAdd
RegDel = registry.RegDel
RmDir = file_system.RmDir
MultiRegDel = registry.MultiRegDel
SetTimer = timers.SetTimer
SetUnattendTimeZone = sysprep.SetUnattendTimeZone
SetupCache = file_system.SetupCache
SpliceDomainJoin = splice.SpliceDomainJoin
ShowChooser = installer.ShowChooser
Shutdown = system.Shutdown
Sleep = installer.Sleep
StartStage = installer.StartStage
Unzip = files.Unzip
UpdateMSU = updates.UpdateMSU
Warn = abort.Warn

ActionError = base.ActionError
ValidationError = base.ValidationError

RestartEvent = base.RestartEvent
ServerChangeEvent = base.ServerChangeEvent
ShutdownEvent = base.ShutdownEvent

# Legacy naming
choice = installer.AddChoice
copy = file_system.MultiCopyFile
driver = drivers.DriverWIM
pull = files.Get
run = files.Execute

