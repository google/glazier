# About StartImage

<!--* freshness: { owner: '@tseknet' reviewed: '2021-04-26' } *-->

Below is a high-level chronological overview of StartImage:

1.  Date/Time check (skip if no network)
1.  Read config (if present)
1.  Partition the OS disk
1.  Apply the FFU image
1.  Copy configs into the OS (if present)
1.  Reboot into the OS

## Launching StartImage

The StartImage binary can be automatically launched via a number of methods
available in WinPE.

The preferred method is to leverage the winpeshl.exe (WinPE Shell) binary that
[launches by default](https://docs.microsoft.com/en-us/windows-hardware/manufacture/desktop/winpeshlini-reference-launching-an-app-when-winpe-starts)
when WinPE starts. The configuration file for the winpeshl.exe binary is
winpeshl.ini. Both are located in `X:\Windows\System32`.

As part of creating your WinPE image, the winpeshl.ini file should include the
required call to StartImage, for example:

```bash
[LaunchApps]
wpeinit
"X:\startimage.exe", --verbose
```

## Flags

TL;DR: Execute `startimage.exe help`

StartImage uses [subcommands](https://github.com/google/subcommands) to
construct command-line flags. These are all defined in `startimage.go`. Flags
enable you to customize your StartImage execution without having to recompile
the binary.

## Testing

Testing changes to StartImage is accomplished via
[GitHub Actions](https://github.com/google/glazier/actions/workflows/go_tests.yml)
performed on every pull and push request.
