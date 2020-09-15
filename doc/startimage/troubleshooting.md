# Startimage Troubleshooting

<!--* freshness: { owner: 'dantsek' reviewed: '2020-09-02' } *-->

[TOC]

## Where is the issue?

The first step in troubleshooting should always be ascertaining where in the
[process](design.md) the problem is occurring.

As part of [hand-off](design#hand-off.md), Startimage may execute other
binaries. Confirm whether the issue is with startimage itself, or with the
script/binary that was executed by Startimage.

## Logs

Everything executed by Startimage will be logged to `X:\startimage.log` file. In
the event of failure, check this log file and review the last thing that was
executed, and work backwards from there.

## Known Errors

Known errors are captured by default via Startimage's error handling. When you
run into a known error, it will be logged to the console and
`X:\startimage.log`. You can identify where in the code this error occured, and
work backwards from there to investigate the issue.

## Unknown Errors

In the event of Startimage running into an undefined error, Go will panic. The
stack trace of the error will be included in this panic. Please gather as much
data as possible and [open an issue](https://github.com/google/glazier/issues)
for further investigation.
