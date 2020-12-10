# Glazier Setup Overview

If you're new to Glazier, the [About Glazier](about.md) document will give a
high-level overview of what Glazier is and how it works.

## Requirements

### Python Requirements

**As of Glazier Release 2.0, Glazier now uses Python 3. Python 2 is no longer
supported.**

Glazier relies on some third-party modules which need to be included with the
Python distribution to enable full functionality. These modules are the property
of their respective owners and not the Glazier developers.

*   absl-py: https://github.com/abseil/abseil-py
*   gwinpy: https://github.com/google/winops/tree/master/gwinpy
    *   Provides various interfaces to Windows subsystems.
*   pyyaml: https://pypi.python.org/pypi/PyYAML

For tests:

*   fakefs: https://pypi.python.org/pypi/pyfakefs
*   mock: https://pypi.python.org/pypi/mock

### Resources

Resource files are non-Python files that are required to enable additional
functionality in Glazier's supporting libraries. These can be distributed with
Glazier's code in the `--resource_path` directory.

*   logo.gif
    *   Required by the chooser library to present a logo inside the Chooser UI.
*   windowsZones.xml: http://cldr.unicode.org
    *   Required by the timezone library.

## Boot Media

You will need to create your boot media. Out of the box, Glazier is known to
support
[WinPE](https://msdn.microsoft.com/en-us/windows/hardware/commercialize/manufacture/desktop/winpe-intro).

When building a WinPE image for use with Glazier, you will need to include:

### Requirements

1.  Any drivers required to enable the local NIC/Video/Storage on the device.
    (network connectivity is necessary to reach the distribution point.
1.  A Python interpreter (see [Python Requirements](#python-requirements))
1.  A copy of the Glazier codebase
1.  For WMI functionality, the
    [WMI package](https://docs.microsoft.com/en-us/windows-hardware/manufacture/desktop/winpe-add-packages--optional-components-reference)
    must be included in WinPE
1.  Add the shutdown command to WinPE (shutdown.exe) if not already included in
    your version of WinPE

### Startup (Bootstrap)

WinPE can be configured to automatically start application(s) using
_winpeshl.exe_, with the configuration in
[winpeshl.ini](https://docs.microsoft.com/en-us/windows-hardware/manufacture/desktop/winpeshlini-reference-launching-an-app-when-winpe-starts).

Example _winpeshl.ini_ that will launch `autobuild.ps1` when WinPE starts:

```powershell
[LaunchApps]
wpeinit
powershell,
Set-ExecutionPolicy -ExecutionPolicy Bypass -Force
powershell, -NoProfile -WindowStyle Maximized -NoExit -NoLogo -File "%PROGRAMFILES%\autobuild.ps1" -InformationAction Continue`
```

Example _autobuild.ps1_ that will configure the environment and launch
`autobuild.py` (Glazier) to begin the imaging process:

```powershell
$env:LOCALAPPDATA = 'X:\'
$PYTHON_EXE = 'X:\python\files\python.exe'
$env:PYTHONPATH = 'X:\src'
Write-Information 'Starting imaging process.'
& $PYTHON_EXE "$env:PYTHONPATH\glazier\autobuild.py" --environment=WinPE --config_server=https://glazier.example.com --resource_path=X:\\resources --preserve_tasks=true
```

*   `--environment`: tells autobuild which host environment it's operating
    under. This is tied to a variety of variables in glazier/lib/constants.py, which
    helps autobuild find files on the local system. You may need to modify
    [constants.py](#constants.py) to fit your environment.
*   `--config_server`: tells autobuild where to find your distribution point.
*   `--resource_path`: is used by certain libraries to locate non-python
    companion files. See [Resources](#resources).
*   `--preserve_tasks`: tells autobuild not to purge the local task list if one
    exists. This allows restarts. Set to false to restart an installation from
    scratch.

TIP: For a full list of Glazier flags, execute `python autobuild.py --helpfull`.
You'll notice a flags are distributed throughout various libraries, are are
documented when defined.

### constants.py

In addition to the startup flags provided by autobuild and its libraries, the
file _glazier/lib/constants.py_ contains several programmatic defaults. You will likely
need to adjust these to match your imaging environment and distribution point.

## Images & Sysprep

At some point during the installation, a Windows image will be applied to disk.
Once the host is rebooted into its new image, Windows will undergo sysprep.
Normally, we will want Autobuild to resume operation after sysprep, so it can
complete post-install configuration tasks.

One way to accomplish this is as follows:

1.  Write a small script to replace the logon shell with the autobuild launcher.

```bash
    %WinDir%\System32\reg.exe add "HKCU\Software\Microsoft\Windows NT\CurrentVersion\Winlogon" /v Shell /t REG_SZ /d "PowerShell.exe -NoProfile -WindowStyle Maximized -NoExit -File C:\Glazier\autobuild.ps1"
```

1.  During the WinPE stage of setup, drop your script to the local disk.

1.  When provisioning the base image, configure automatic logon and use
    [LogonCommands](https://msdn.microsoft.com/en-us/windows/hardware/commercialize/customize/desktop/unattend/microsoft-windows-shell-setup-logoncommands)
    to reference the script you saved to disk.

During the following login, your script will replace the logon shell, then
reboot into Autobuild. Autobuild should resume where it left off, processing the
task list.

As one of the final steps in your config, remove the custom logon shell before
rebooting into the completed host.

## Distribution Point

Glazier requires a web-based repository of binary and image files to be
available over HTTP(S). You can use any web server or platform that suits your
needs.

Inside the root of your web host, create two directories: the config root and
the binary root.

### Config Root

The configuration root must contain at minimum one `build.yaml` file. In a
mature system, this directory will likely contain a variety of branching config
files and scripts (example: dev/prod top-level directories).

We recommend keeping the entire contents of the config root in source control,
and exporting it out to the web service whenever changes are made.

The `--config_root_path` flag determines where under `--config_server` this data
is located.

See [Configuration Layout](config_layout.md) for additional information.

### Binary Root

The binary root is a separate directory structure used to hold non-text data.
This split serves to draw a clear boundary between files which may be sourced
from version control, and those which may instead live in mass storage
elsewhere.

We recommend using an organized tree structure to make binaries easy to locate.

```bash
ROOT
├───Company1
│   └───Product1
│       ├───v1
│       └───v2
├───Company2
│   └───Product1
│       └───v1
└───...
```

The `--binary_root_path` flag determines where under `--config_server` this
directory is located.

In config syntax, the binary root is referenced by prefacing a file name and
path with the `@` symbol.

## Example Config

This example gives a concept for a basic `build.yaml`.

```yaml
templates:
  apply_img:
    - Get:
      - ['@MyRepo/WIM/2021_10_01/Windows10.wim',
         'C:\base.wim',
         'ae0666f161fed1a5dde998bbd0e140550d2da0db27db1d0e31e370f2bd366a57']
    - Execute:
      - ['X:\Write-WindowsImage.ps1']

controls:
  - Get:
      - ['partition.ps1', 'X:\partition.ps1']
      - ['apply_image.ps1', 'X:\apply_image.ps1']

  - Execute:
    - ['X:\partition.ps1']

  - template:
    - apply_img

  - ExitWinPE: []

  - include:
    - ['drivers/', 'build.yaml']
    - ['applications/', 'build.yaml']

  - Reboot: [10, 'Rebooting to complete setup. The machine will be ready to use.']
```

This config retrieves two hypothetical `.ps1` files from the config root
(`partition.ps1`, and `apply_image.ps1`). It executes `partition.ps1` to
partition the local disk. It then invokes the template *apply_img*, which
retrieves a WIM file from the binary root, and executes `apply_image.ps1`. It
calls the action `ExitWinPE`, at which point the system would reboot (presumably
into sysprep). After sysprep, the task list would resume processing with
whatever commands were obtained from the contents of the `drivers/build.yaml`
and `applications/build.yaml` files (for illustration - not shown here).
Finally, the host would reboot.

More information about configuration files is available in the
[Glazier Build YAML Specification](../yaml).
