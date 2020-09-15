# Startimage


[TOC]

Startimage is a standalone binary, written in Go, that identifies and sets the
necessary parameters required to start the Glazier imaging process.

## Background

Glazier takes a supported physical (or virtual) device, applies a somewhat
vanilla copy of the Windows operating system, and layers in your preferred
management stack. The first stage of imaging a machine via Glazier is booting
into the Windows Preinstallation Environment (WinPE). WinPE is a lightweight
Windows environment that can be loaded directly into RAM. The WinPE image can be
loaded from PXE or bootable ISO image.

## How It Works

Below is a high-level, chronological overview of the steps taken by the
Startimage binary. See the [design documentation](design.md) or click any item
below for a more detailed explanation.

1.  [Downloading Configs](design.md#downloading-configs) (optionally)
    [using SignedURLs](design.md#using-signedurls)
1.  [Reading configs](design.md#reading-configs)
1.  [Filter configs](design.md#filter-configs)
1.  [Syncing Time](design.md#syncing-time)
1.  [Prompting the User](design.md#prompting-the-user)
1.  [Verify latest version](design.md#verify-latest-version)
1.  [Set Registry Keys](design.md#set-registry-keys)
1.  [Handoff](design.md#handoff)

## Getting Started

TODO: Define or link to common flags.

`startimage.exe` can be executed with several flags, defined in the code itself.
Some flags are mandatory to start Glazier. Startimage flags were written to
enable you to customize your Glazier configuration without having to recompile
the code.

Example Startimage execution with custom flags:

```powershell
./startimage.exe --alsologtostderr --debug --registry_root "SOFTWARE\Glazier" trusted --config_server "https://glazier.com"
```

See [example commands](build.md#example-commands) for a more detailed breakdown
of the examples listed above.

## Building and Testing

See the [build documentation](build.md) for information on how you can build and
test changes to Startimage.

## Troubleshooting

See the [troubleshooting documentation](troubleshooting.md) for information on
what to do if you run into issues executing Startimage.
