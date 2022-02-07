# StartImage

<!--* freshness: { owner: '@tseknet' reviewed: '2021-04-26' } *-->

StartImage is a standalone binary written in Go with the ultimate goal of
applying an
[Full Flash Update](https://docs.microsoft.com/en-us/windows-hardware/manufacture/desktop/deploy-windows-using-full-flash-update--ffu)
(FFU) image to the disk and rebooting into the Operating System (OS). For a chronological overview of the steps taken by the
StartImage binary, see the [about](about.md) page.

## Usage

```powershell
# Get a list of flags
startimage.exe help

# Launch StartImage with verbose logging
startimage.exe --verbose
```

## Troubleshooting

### Where is the issue?

The first step in troubleshooting should always be ascertaining where in the
[process](about.md) the problem is occurring. StartImage files such as logs, configs, etc. live under the `%TEMP%\StartImage` directory.

### Need Help?

In the event of StartImage running into an undefined error, Go will panic. The
stack trace of the error will be included in this panic. Please gather as much
data as possible and [open an issue](https://github.com/google/glazier/issues)
for further investigation.
