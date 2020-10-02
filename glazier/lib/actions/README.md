# Glazier Installer Actions



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

### ChangeServer

Change the active Glazier config server at runtime.

ChangeServer is a unique action in the sense that it alters the behavior of the
configuration builder in real time. This action must come (logically) last in
the input config; once reached, the config builder effectively restarts immediately
with the new server address and root. No subsequent tasks in the original
location will be handled.

#### ChangeServer Arguments

*   Format: List
    *   Arg1[str]: The config server to override the config_server flag.
    *   Arg2[str]: The config root path to override the config_root_path flag.

#### Examples

    ChangeServer: ['https://new-server.example.com', '/new/config/path']

### CopyDir

Copy directories from source to destination.

#### CopyDir Arguments

*   Format: List
    *   Arg1[str]: Source directory path
    *   Arg2[str]: Destination directory path.
    *   Arg3[bool]: Delete existing directory before copying. (optional)

#### Examples

    CopyDir: ['X:\Glazier', 'C:\Glazier\Old']
    CopyDir: ['X:\Glazier', 'C:\Glazier\Old', true]

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
        *   ArgE[bool]: Log console output ONLY to the shell.
            *   Default: False
    *   Arg2[list]: The second command to execute. (optional)
    *   ...

#### Examples

    Execute: [
      # Using defaults.
      ['C:\Windows\System32\netsh.exe interface teredo set state disabled'],
      # 0 or 1 are successful exit codes, 3010 will trigger a restart.
      ['C:\Windows\System32\msiexec.exe /i @Drivers/HP/zbook/HP_Hotkey_Support_6_2_20_8.msi /qn /norestart', [0,1], [3010]],
      # 0 is a successful exit code, 2 will trigger a restart, and True will rerun the command after the restart.
      ['C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -NoLogo -NoProfile -File #secureboot.ps1', [0], [2], True]
      # 0 is a successful exit code, 2 will trigger a restart, and True will ONLY log output to console.
      ['C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -NoLogo -NoProfile -File #secureboot.ps1', [0], [2], False. True]
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

### GooGetInstall

Installs one or more GooGet packages with optional arguments.

Supports multiple packages via nested list structure.

#### GooGetInstall Arguments

*   Format: List
    *   Arg1[str]: The first GooGet package to install
        *   ArgA[str]: GooGet package name
        *   ArgB[list]: All other arguments to googet.exe. This includes repo
            URLs, -reinstall, -redownload, etc.
            *   If the % character is used in ArgB, it will be replaced for the
                current build branch, taken from glazier/lib/buildinfo.
        *   ArgC[str]: googet.exe location (optional)
        *   ArgD[int]: Installation retry attemps (optional, defaults to 5)
        *   ArgE[int]: Installation retry sleep interval in seconds (optional,
            defaults to 30)
    *   Arg2[str]: The second GooGet package to install (optional)
    *   ...

#### Examples

```yaml
    GooGetInstall: [
      # Specify only GooGet package name
      ['test_package_v1'],
      # Package name with additional GooGet arguments
      ['test_package_v1', ['http://example.com/team-unstable, http://example.co.uk/secure-unstable, https://example.jp/unstable/ -reinstall whatever']],
      # Package name, no GooGet arguments, but with custom path to googet.exe
      ['test_package_v1', [], 'C:\ProgramData\GooGet\googet.exe'],
      # Package name, custom GooGet arguments, and custom path to googet.exe
      ['test_package_v1', ['http://example.com/team-unstable, http://example.co.uk/secure-unstable, https://example.jp/unstable/ -reinstall whatever'], 'C:\ProgramData\GooGet\googet.exe'],
      # Package name with custom retry count of 3 and sleep interval of 60 seconds
      ['test_package_v1', [], , 3, 60],
      # Replaces '%' in custom GooGet arguments with the current build branch
      ['test_package_v1', ['http://example.com/team-%, http://example.co.uk/secure-%, https://example.jp/%/ -reinstall whatever'], 'C:\ProgramData\GooGet\googet.exe'],
    ]
```

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

### PSCommand/MultiPSCommand

Run a PowerShell command.

#### PSCommand Arguments

*   Format: List
    *   Arg1[str]: The PowerShell command to be run.
    *   Arg2[list]: One or more integers indicating successful exit codes.
          *   Default: [0]
    *   Arg3[list]: One or more integers indicating a reboot is required.
        *   Default: []
    *   Arg4[bool]: Rerun after a reboot occurs. A reboot code must be
        provided and returned by the execution.
          *   Default: False
    *   Arg5[bool]: Log console output ONLY to the shell. Ignores log=True.
        *   Default: False
    *   Arg6[bool]: Log messages to Python stdout. Only valid if shell=False.
          *   Default: True

#### MultiPSCommand Arguments

*    Format: List of Lists
     *  Arg1[List]: First [PSCommand Argument](#pscommand-arguments) list.
     *  Arg2[List]: Second [PSCommand Argument](#pscommand-arguments) list.
     *  ...

#### Examples

```yaml
    # Specify only the PowerShell script.
    PSCommand: ['Write-Verbose Foo -Verbose']

    # 0 or 1 as successful exit codes.
    PSCommand: ['Write-Verbose Foo -Verbose', [0, 1]]

    # 1337 will trigger a restart.
    PSCommand: ['Write-Verbose Foo -Verbose', [0, 1], [1337]]

    # True will rerun the command after restart.
    PSCommand: ['Write-Verbose Foo -Verbose', [0, 1], [1337], True]

    # True will ONLY log PowerShell output to console.
    PSCommand: ['Write-Verbose Foo -Verbose', [0, 1], [1337], True, True]

    # Will not any log PowerShell output.
    PSCommand: ['Write-Verbose Foo -Verbose', [0, 1], [1337], True, False, False]

    MultiPSCommand:
      - ['Write-Information "Setting Execution Policy"']
      - ['Set-ExecutionPolicy -ExecutionPolicy RemoteSigned', [0], [1337]]

```

### PSScript/MultiPSScript

Run a PowerShell script file using the local PowerShell interpreter.

#### PSScript Arguments

*   Format: List
      *   Arg1[str]: The script file name or path to be run..
      *   Arg2[list]: A list of strings to be passed to the script as parameters.
          * Default: []
      *   Arg3[list]: One or more integers indicating successful exit codes.
          *   Default: [0]
      *   Arg4[list]: One or more integers indicating a reboot is required.
          *   Default: []
      *   Arg5[bool]: Rerun after a reboot occurs. A reboot code must be
          provided and returned by the execution.
          *   Default: False
      *   Arg6[bool]: Log console output ONLY to the shell. Ignores log=True.
          *   Default: False
      *   Arg7[bool]: Log messages to Python stdout. Only valid if shell=False.
          *   Default: True


#### MultiPSScript Arguments

*    Format: List of Lists
     *  Arg1[List]: First [PSScript argument](#psscript-arguments) list.
     *  Arg2[List]: Second [PSScript argument](#psscript-arguments) list.
     *  ...

#### Examples

```yaml
    # Specify only the PowerShell script.
    PSScript: ['#Sample-Script.ps1']

    # Additional parameters.
    PSScript: ['#Sample-Script.ps1', ['-Verbose', '-InformationAction', 'Continue']]

    # 0 or 1 as successful exit codes.
    PSScript: ['#Sample-Script.ps1', ['-Verbose', '-InformationAction', 'Continue'], [0,1]]

    # 1337 will trigger a restart.
    PSScript: ['#Sample-Script.ps1', ['-Verbose', '-InformationAction', 'Continue'], [0,1], [1337]]

    # True will rerun the command after restart.
    PSScript: ['#Sample-Script.ps1', ['-Verbose', '-InformationAction', 'Continue'], [0,1], [1337], True]

    # True will ONLY log PowerShell output to console.
    PSScript: ['#Sample-Script.ps1', ['-Verbose', '-InformationAction', 'Continue'], [0,1], [1337], True, True]

    # Will not any log PowerShell output.
    PSScript: ['#Sample-Script.ps1', ['-Verbose', '-InformationAction', 'Continue'], [0,1], [1337], True, False, False]

    MultiPSScript:
      - ['#Sample-Script.ps1']
      - ['#Sample-Script.ps1', ['-Verbose', '-InformationAction', 'Continue'], [0,1], [1337], True, False, False]

```

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
    *   Arg2[list]: Second key to add (optional)
    *   ...

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
    *   Arg2[list]: Second key to add (optional)
    *   ...

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
    *   Arg3[bool]: Whether to remove the next item in the task list as well.
        (Optional)

#### Examples

    Reboot: [30]
    Reboot: [10, "Restarting to finish installing drivers."]
    Reboot: [10, "Restarting to finish installing drivers.", True]

### RmDir

Remove one or more directories.

#### Arguments

*   Format: List
    *  Arg1[Str]: First directory to be removed
    *  ...

#### Examples

    RmDir: ['C:\Glazier_Cache', 'D:\Glazier_Cache']

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
    *   Arg3[bool]: Whether to remove the next item in the task list as well.
        (Optional)

#### Examples

    Shutdown: [30]
    Shutdown: [10, "Shutting down to save power."]
    Shutdown: [10, "Shutting down to save power.", True]

### Sleep

Pause the installer.

#### Arguments

*   Format: List
    *   Arg1[int]: Duration to sleep.
    *   Arg2[str]: The reason/message for the sleep. (Optional)

#### Examples

    Sleep: [30]
    Sleep: [300, "Waiting for Group Policy to apply..."]

### StartStage

Start a new stage of the imaging process.

Stages are used for tracking (internally and externally) and reporting progress
through the imaging process.

#### Arguments

*   Format: List
    *   Arg1[int]: Stage number
    *   Arg2[bool]: If True, indicates a terminal stage (the last stage of the build). The action will set both the start and end time on the stage, assuming no subsequent stages are yet to come. (optional)

#### Examples

    StartStage: [1]

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
