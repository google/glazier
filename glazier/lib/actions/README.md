# Glazier Installer Actions

[TOC]

Actions are classes which the configuration handler may call to perform a
variety of tasks during imaging.

## Usage

Each module should inherit from BaseAction and will receive a BuildInfo instance
(self.\_build_info).

Arguments are stored as a data structure in the self.\_args variable, commonly
as an ordered list or dictionary.

Each action class should override the Run function to execute its main behavior.

If an action fails, the module should raise ActionError with a message
explaining the cause of failure. This will abort the build.

## Validation

Config validation can be accomplished by overriding the Validate() function.
Validate should test the inputs (\_args) for correctness. If \_args contains any
unexpected or inappropriate data, ValidationError should be raised.

Validate() will pass for any actions which have not overridden it with custom
rules.

## Actions

### Abort

Aborts the build with a custom error message.

#### Arguments

*   Format: List
    *   Arg1[str]: An error message to display; the reason for aborting.

### AddChoice

Aliases: choice

### BitlockerEnable

Enable Bitlocker on the host system.

Available modes:

*   ps_tpm: TPM via PowerShell
*   bde_tpm: TPM via manage-bde.exe

#### Arguments

*   Format: List
    *   Arg1[str]: The mode to use for enabling Bitlocker.

### BuildInfoDump

Write state from the BuildInfo class to disk for later processing by
BuildInfoSave.

### BuildInfoSave

Load BuildInfo data from disk and store permanently to the registry.

### CopyDir

Copy directories from source to destination.

#### CopyDir Arguments

*   Format: List
    *   Arg1[str]: Source directory path
    *   Arg2[str]: Destination directory path.

### CopyFile/MultiCopyFile

Copy files from source to destination.

Also available as MultiCopyFile for copying larger sets of files.

#### CopyFile Arguments

*   Format: List
    *   Arg1[str]: Source file path
    *   Arg2[str]: Destination file path.

#### MultiCopyFile Arguments

*   Format: List
    *   Arg1[list]: First set of files to copy
        *   Arg1[str]: Source file path
        *   Arg2[str]: Destination file path.
    *   Arg2[list]: Second set of files to copy
        *   Arg1[str]: Source file path
        *   Arg2[str]: Destination file path.
    *   ...

#### Examples

    CopyFile: ['X:\glazier.log', 'C:\Windows\Logs\glazier.log']

    MultiCopyFile:
      - ['X:\glazier-applyimg.log', 'C:\Windows\Logs\glazier-applyimg.log']
      - ['X:\glazier.log', 'C:\Windows\Logs\glazier.log']

### DomainJoin

Joins the host to the domain. (Requires installer to be running within the host
OS.)

#### Arguments

*   Format: List
    *   Arg1[str]: The desired method to use for the join, as defined by the
        domain join library.
    *   Arg2[str]: The name of the domain to join.
    *   Arg3[str]: The OU to join the machine to. (optional)

#### Example

    DomainJoin: ['interactive', 'domain.example.com']
    DomainJoin: ['auto', 'domain.example.com', 'OU=Servers,DC=DOMAIN,DC=EXAMPLE,DC=COM']

### Driver

Process drivers in WIM format. Downloads file, verifies hash, creates an empty
directory, mounts wim file, applies drivers to the base image, and finally
unmounts wim.

#### Example

    Driver: ['@/Driver/HP/z840/win10/20160909/z840.wim',
             'C:\Glazier_Cache\z840.wim',
             'cd8f4222a9ba4c4493d8df208fe38cdad969514512d6f5dfd0f7cc7e1ea2c782']

### Execute

Run one or more commands on the system.

Supports multiple commands via nested list structure due to the frequency of
program executions occurring as part of a typical imaging process.

#### Arguments

*   Format: List
    *   Arg1[list]: The first command to execute
        *   ArgA[str]: The entire command line to execute including flags.
        *   ArgB[list]: One or more integers indicating successful exit codes.
            *   Default: [0]
        *   ArgC[list]: One or more integers indicating a reboot is required.
            *   Default: []
        *   ArgD[bool]: Rerun after a reboot occurs. A reboot code must be
            provided and returned by the execution.)
            *   Default: False
    *   Arg2[list]: The second command to execute. (optional)
    *   ...

#### Examples

    Execute: [
      # Using defaults.
      ['C:\Windows\System32\netsh.exe interface teredo set state disabled'],
      # 0 or 1 are successful exit codes, 3010 will trigger a restart.
      ['C:\Windows\System32\msiexec.exe /i @Drivers/HP/zbook/HP_Hotkey_Support_6_2_20_8.msi /qn /norestart', [0,1], [3010]],
      # 0 is a successful exit code, 2 will trigger a restart, and 'True' will rerun the command after the restart.
      ['C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -NoLogo -NoProfile -File #secureboot.ps1', [0], [2], True]
    ]

### ExitWinPE

Leave the WinPE environment en route to the local host configuration. Is
normally followed by sysprep, then the relaunch of the autobuild tool running
inside the new host image.

Performs multiple steps in one:

*   Copies the autobuild executable to C:
*   Copies the acting task list to C:
*   Reboots the host

Without a separate command, some of these actions would remain in the task list
after being carried over, and would be re-executed.

#### Arguments

*   None

### Get

Aliases: pull

Downloads remote files to local disk. Get is an ordered, two dimensional list of
source file names and destination file names. Source filenames are assumed to be
relative to the location of the current yaml file.

#### Verification

To use checksum verification, add the computed SHA256 hash as a third argument
to the list. This argument is optional, and being absent or null bypasses
verification.

    Get:
        - ['windows10.wim', 'c:\base.wim', '4b5b6bf0e59dadb4663ad9b4110bf0794ba24c344291f30d47467d177feb4776']

#### Arguments

*   Format: List
    *   Arg1[list]: The first file to retrieve.
        *   ArgA[str]: The remote path to the source file.
        *   ArgB[str]: The local destination path for the file.
        *   ArgC[str]: The sha256 sum of the flie for verification. (optional)
    *   Arg2[list]: The second file to retrieve. (optional)
    *   ...

#### Examples

    Get:
        - ['win2008-x64-se.wim', 'c:\base.wim']
        - ['win2008-x64-se.wim.sha256', 'c:\base.wim.sha256']

### GoogetInstall

Installs a package via Googet with optional arguments.

#### GoogetInstall Arguments

*   Format: List
    *   Arg1[str]: Package name
    *   Arg2[list]: All other arguments. This includes repo URLS, -reinstall, -redownload, etc. (optional)
      * If the % character is used in Arg3, it will be replaced for the current build branch, taken from glazier/lib/buildinfo.
    *   Arg3[str]: Googet binary location (optional)

#### Examples

    GoogetInstall: ['test_package_v1']

    GoogetInstall: ['test_package_v1', ['http://example.com/team-unstable, http://example.co.uk/secure-unstable, https://example.jp/unstable/ -reinstall whatever']]

    GoogetInstall: ['test_package_v1', [], 'C:\ProgramData\Googet\Googet.exe']

    GoogetInstall: ['test_package_v1', ['http://example.com/team-unstable, http://example.co.uk/secure-unstable, https://example.jp/unstable/ -reinstall whatever'], 'C:\ProgramData\Googet\Googet.exe']

    GoogetInstall: ['test_package_v1', ['http://example.com/team-%, http://example.co.uk/secure-%, https://example.jp/%/ -reinstall whatever'], 'C:\ProgramData\Googet\Googet.exe']


### LogCopy

Attempts to copy a log file to a new destination for collection.

Destinations include Event Log and CIFS. Copy failures only produce warnings
rather than hard failures.

Logs will always be copied to the local Application log. Specifying the second
logs share parameter will also attempt to copy the log to the specified file
share.

#### Arguments

*   Format: List
    *   Arg1[str]: Full path name of the source log file.
    *   Arg2[str]: The path to the destination file share. (optional)

#### Examples

    LogCopy: ['C:\Windows\Logs\glazier.log', '\\shares.example.com\logs-share']

### MkDir

Make a directory.

#### Arguments

*   Format: List
    *   Arg1[str]: Full path name of directory

#### Examples

    MkDir: ['C:\Glazier_Cache']

### PSScript

Run a PowerShell script file using the local PowerShell interpreter.

#### Arguments

*   Format: List
    *   Arg1[str]: The script file name or path to be run.
    *   Arg2[list]: A list of flags to be supplied to the script. (Optional)

#### Examples

    PSScript: ['#Sample-Script.ps1']

    PSScript: ['C:\Sample-Script2.ps1', ['-Flag1', 123, '-Flag2']]

### RegAdd/MultiRegAdd

Create/modify a registry key.

Also available as MultiRegAdd for creating larger sets of registry keys.

#### RegAdd Arguments

*   Format: List
    *   Arg1[str]: Root key
    *   Arg2[str]: Key path
    *   Arg3[str]: Key name
    *   Arg4([str] or [int]): Key value
    *   Arg5[str]: Key type (REG_SZ or REG_DWORD)
    *   Arg6[bool]: Use 64bit Registry (Optional)

#### MultiRegAdd Arguments

*   Format: List
    *   Arg1[list]: First Key to add
        *   ArgA[str]: Root key
        *   ArgB[str]: Key path
        *   ArgC[str]: Key name
        *   ArgD([str] or [int]: Key value
        *   ArgE[str]: Key type (REG_SZ or REG_DWORD)
        *   ArgF[bool]: Use 64bit Registry (Optional)
    *  Arg2[list]: Second key to add (optional)
    *  ...

#### Examples

    RegAdd: ['HKLM', 'SOFTWARE\Microsoft\Windows NT\CurrentVersion\SoftwareProtectionPlatform', 'KeyManagementServiceName', 'kms.example.com', 'REG_SZ']

    MultiRegAdd:
      - ['HKLM', 'SOFTWARE\Policies\Microsoft\WindowsStore', 'RemoveWindowsStore', 1, 'REG_DWORD']
      - ['HKLM', 'SOFTWARE\Policies\Microsoft\Windows\Windows Search', 'AllowCortana', 0, 'REG_DWORD']

### RegDel/MultiRegDel

#### RegDel Arguments
Delete a registry key.

*   Format: List
    *   Arg1[str]: Root key
    *   Arg2[str]: Key path
    *   Arg3[str]: Key name
    *   Arg4[bool]: Use 64bit Registry (Optional)

#### MultiRegDel Arguments

*   Format: List
    *   Arg1[list]: First Key to add
        *   ArgA[str]: Root key
        *   ArgB[str]: Key path
        *   ArgC[str]: Key name
        *   ArgD[bool]: Use 64bit Registry (Optional)
    *  Arg2[list]: Second key to add (optional)
    *  ...

#### Examples

    RegDel: ['HKLM', 'SOFTWARE\Microsoft\Windows NT\CurrentVersion\SoftwareProtectionPlatform', 'KeyManagementServiceName']

    MultiRegDel:
      - ['HKLM', 'SOFTWARE\Policies\Microsoft\WindowsStore', 'RemoveWindowsStore']
      - ['HKLM', 'SOFTWARE\Policies\Microsoft\Windows\Windows Search', 'AllowCortana']

### Reboot

Restart the host machine.

#### Arguments

*   Format: List
    *   Arg1[int]: The timeout delay until restart occurs.
    *   Arg2[str]: The reason/message for the restart to be displayed.
        (Optional)

#### Examples

    Reboot: [30]
    Reboot: [10, "Restarting to finish installing drivers."]

### SetUnattendTimeZone

Attempts to detect the timezone via DHCP and configures any \<TimeZone\> fields
in unattend.xml with the resulting values.

#### Arguments

*   None

### SetupCache

Creates the imaging cache directory with the path stored in BuildInfo.

#### Arguments

*   None

#### Examples

    SetupCache: []

### SetTimer

Add an imaging timer.

#### Arguments

*   Format: List
    *   Arg1[str]: Timer name

#### Examples

    SetTimer: ['TimerName']

### ShowChooser

Show the Chooser UI to display all accumulated options to the user. All results
are returned to BuildInfo and the pending options list is cleared.

#### Arguments

*   None

### Shutdown

Shutdown the host machine.

#### Arguments

*   Format: List
    *   Arg1[int]: The timeout delay until shutdown occurs.
    *   Arg2[str]: The reason/message for the shutdown to be displayed.
        (Optional)

#### Examples

    Shutdown: [30]
    Shutdown: [10, "Shutting down to save power."]

### Sleep

Pause the installer.

#### Arguments

*   Format: List
    *   Arg1[int]: Duration to sleep.

#### Examples

    Sleep: [30]

### Unzip

Unzip a zip file to the local filesystem.

#### Arguments

*   Format: List

    *   Arg1[str]: Path to the zip file.
    *   Arg2[str]: Path to extract the zip file to.

#### Examples

    Unzip: ['C:\some_archive.zip', 'C:\Some\Destination\Path']

### UpdateMSU

Process updates in MSU format. Downloads file, verifies hash, creates a
SYS_CACHE\Updates folder that is used as a temp location to extract the msu
file, and applies the update to the base image.

#### Example

    Update: ['@/Driver/HP/z840/win7/20160909/kb290292.msu',
             'C:\Glazier_Cache\kb290292.msu',
             'cd8f4222a9ba4c4493d8df208fe38cdad969514512d6f5dfd0f7cc7e1ea2c782']

### Warn

Issue a warning that can be bypassed by the user.

#### Arguments

*   Format: List
    *   Arg1[string]: Message to the user.

#### Examples

    Warn: ["You probably don't want to do this, or bad things will happen."]
