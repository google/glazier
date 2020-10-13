# About Glazier

This document outlines the basic operating principles of Glazier.

## Overview

From a high level, any imaging system does some variation of the following:

*   Boots the physical (or virtual) device into a working environment
*   Applies an operating system to permanent storage attached to the device
*   Performs customization of said operating system

Glazier is no different. Glazier's [Autobuild](#autobuild) tool provides a means
of dynamically selecting the image(s), application(s), and configuration(s) to
be applied to a host. It retrieves any required files over the network, executes
scripts and binaries, and modifies the host as required.

Glazier is heavily network-based. Rather than attempt to provide complete,
pre-configured operating system images, which are laborious to maintain, Glazier
emphasizes maintaining basic images, and distributing all required customization
via the network.

Glazier has no graphical interface. Glazier focuses on keeping all data about
the imaging process exposed to the administrator, where it is most accessible
and most powerful.

A Glazier environment will consist of a minimum of:

*   One boot image containing Python and the Glazier tools
*   One HTTP server host to distribute configs, scripts, and binaries
*   One set of configs and associated scripts and binaries

## First Boot

Regardless of the platform, imaging requires a working host environment capable
of running the installation tools. Glazier can theoretically run from any type
of boot environment, but it was designed to work with
[WinPE](https://msdn.microsoft.com/en-us/windows/hardware/commercialize/manufacture/desktop/winpe-intro).

WinPE gives us all the capabilities needed to discover information about the
local host (as Windows will see it), retrieve our installation files, and
bootstrap the install process. Customizing a PE environment is fairly simple and
familiar to most Windows administrators. PE images can be distributed via the
network (PXE boot), via file (ISO), or portable storage (USB, etc).

Because Glazier is Python-based, the PE or other boot media must contain a
Python interpreter. You can place the Glazier code and dependencies directly in
the PE, or for more advanced users, you can write a custom launcher to
accomplish this.

WinPE should be configured to automatically launch the installer tool. For
Glazier, this is usually Autobuild \(autobuild.py\).

### Custom Launchers (Advanced)

Producing a new PE image can be an error-prone and time-consuming process.
Glazier is a network-based system and follows the general model that most files
needed for installation can be retrieved at install time. The theory is that it
is much easier to change network-based files in a controlled, predictable, and
low-overhead way than it is to regenerate a WIM or PE image containing the same
changes. In other words, we always attempt to minimize the need to generate new
boot images by pushing most routine changes into Glazier's dynamic environment.

For advanced users, we recommend creating a simple launcher which will run
directly from _winpeshl.exe_ that leverages the configuration file
(_winpeshl.ini_) to retrieve the initial files required from a web server. This
prevents the need to generate a new PE if any changes are required to Python,
Glazier, or any other bundled dependencies.

## Autobuild

Autobuild is the central component of the Glazier system. It contains the logic
for host discovery, file retrieval, configuration handling, and for implementing
several basic installation actions.

When first run, Autobuild should be directed, via a command-line flag, to the
web server hosting the installation configuration files. It will retrieve the
root configuration file and begin parsing it. Glazier will compare the commands
it finds in these files to what it discovers about the state of the host
(hardware, network, etc). It may also be configured to prompt the user for
input.

Based on the configuration files and the host state, Autobuild prepares a
chronological list of actions. This list of actions instructs every operation
performed via Glazier to producing a fully provisioned device.

Once autobuild has reached the end of the available configuration files, it will
have produced a list of pending actions for the localhost. It will then begin
executing them in order. It will end when the last action is completed, or any
of the required actions fail.

## Configuration Flow

Autobuild's ability to handle configuration is entirely freeform. It could
easily be used for tasks other than imaging. In the case of imaging, a
successful configuration will tend to follow a common series of events, but
these are entirely up to the administrator:

1.  Boot into WinPE and launch Autobuild.
1.  Prompt the user for input, if needed, to gather facts about the desired
    state.
1.  Retrieve an operating system image.
1.  Retrieve any drivers necessary to customize the image and apply them.
1.  Partition the disk and apply the image.
1.  Stage the Glazier code, Python, and any other supporting files inside the
    new disk.
1.  Reboot into the configured OS and run Sysprep.
1.  Reboot into Glazier to perform detailed host customization
    *   Install applications
    *   Install drivers
    *   Customize the OS
    *   Etc.
1.  Clean up any remaining installation files, and reboot into the finished
    host.

It will take time to build a complete end-to-end configuration for the first
time. However, subsequent changes are often trivial, and it becomes very simple
to branch into different configurations once you have a working foundation, as
explained below.

## Configuration Files

The [Glazier Build YAML Specification](../yaml) page goes into detail about the
format of Glazier's configuration files.

"Text files" may seem like a surprising foundation for an imaging system,
however, they are ultimately one of the most powerful and flexible options
available. GUI-based systems limit the administrator to only the features and
capabilities built into the GUI by the manufacturer. The "data" held behind the
GUI is often obscured and inaccessible.

With Glazier, the configuration files hold your imaging data in raw and
unrestricted form. Autobuild will parse them, but how you choose to manage them
may grant numerous additional benefits.

### Editors

You can modify Glazier configs in the text editor of your choice, meaning
thousands of options are available, for free, on any platform. Because YAML is
an open standard, any text editor with YAML support will give additional
benefits, such as automatic syntax highlighting.

### Version Control

Like computer code, Glazier's text files are a perfect fit for a version control
system \(VCS\). It is highly recommended to maintain your Glazier configuration
tree \(and any associated scripts\) inside a VCS. This produces many immediate
benefits to the administrator, including:

*   A complete revision history of your imaging environment
*   The ability to immediately roll back to an earlier configuration
*   The ability to implement peer review of changes, exactly as may be done for
    code

### Branching

A simple Glazier deployment will involve a single configuration root, which may
be all that is required for small environments. Larger or more sensitive
environments will want to employ QA procedures. This is trivial with Glazier's
text-based format, and particularly so when combined with a version control
system.

Create multiple "root" directories, such as unstable, testing, and stable. Make
initial changes in the unstable root, and deploy them to testing and stable.
Once vetted, the configuration files can be copied or integrated over to the
next least stable branch, and so on. Changes can be cherry-picked across
branches, and the text files allow for simple diffs and patches that are easily
reviewed.

### Simulation & Test

Autobuild is the core consumer of config files in the Glazier system, but
because the text files are based on the open YAML standard, administrators can
implement new configuration parsers in any language or platform that they like.

One practical use of this is test frameworks: it is simple to write code which
will consume configuration files for the sake of performing build testing or
configuration auditing.

Another option is build simulation. Configs can be parsed and charted, graphed,
or printed to observe their behavior when given arbitrary inputs, with no need
to involve physical hardware or the delays inherent in performing an actual host
installation.

## File Distribution

Glazier relies heavily on HTTP(S) as its mechanism for the distribution of
content. \(We refer to HTTP and HTTPS interchangeably. However, HTTPS is
required for Glazier to operate correctly.\) HTTP was chosen for a variety of
reasons, including:

*   It is an open and ubiquitous protocol
*   There are numerous freely available implementations of HTTP servers
*   There are well-established methods for globally distributing data over HTTP;
    it scales
*   In the case of HTTPS, it is considered highly secure

In a Glazier environment, the web servers host nearly all content except for the
initial boot media. This will include all configuration files, as well as
binaries (installers, images, etc) and scripts. As Autobuild executes, it
retrieves these files on demand.

It is up to the administrator to decide how exactly to structure the files
within the web service, as well as how to deploy the files to the web service.
In a test environment, the administrator may simply place and edit the files
directly within the web host. In a production environment, it is recommended to
develop a more formal "deployment" system; ideally, one which can synchronize
content from a version control system directly to the web host.

## Python

Glazier is implemented in Python, which is free and cross-platform. Parts of
Glazier does depend on Windows-specific functionality, such as WMI. This does
not mean it cannot be ported to run from other OSes, however, this will require
extra effort.

Python requires an interpreter to be available within the OS while Glazier is
running. Python interpreters for Windows are freely available.

Glazier is not compiled code. Anyone can open Glazier's Python files and edit
them. This is one of the great strengths of Glazier: with a little knowledge of
Python, you can easily extend Glazier with custom functionality.

### Glazier Actions

When it comes to the act of imaging a system, most of Glazier's time is spent
performing Actions. Glazier ships with several core Actions, which are
documented in the [Actions README](../../glazier/lib/actions).

Adding new Glazier Actions is meant to be as simple as possible. Actions are
automatically recognized by Autobuild's configuration handler. An administrator
need only drop a new Python class into the actions module, and the new command
becomes immediately accessible for use in config files.

Action classes also expose an (optional) validation capability. This can be
integrated with a unit test framework to provide real-time validation of
configuration files.

### Other Languages

Administrators may prefer to implement some parts of the imaging process in
other languages, such as PowerShell, Batch, Go, etc. This is
perfectly fine, fully supported, and in some cases even recommended.

As described above, Glazier's Autobuild tool is essentially a command executor.
It works great out of the box with companion scripts or executables and can
recognize success or failure conditions based on return codes. For more complex
interactions, custom Actions can easily wrap external scripts and executables.
