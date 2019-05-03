# Glazier

Glazier [noun]: a person who installs windows.

## What is Glazier?

**Glazier** is a tool developed at Google for automating the installation of the Microsoft Windows operating system on various device platforms.

At a high level, any imaging system does some variation of the following:

*   Boots the device into a working environment
*   Applies an operating system to permanent storage attached to the device
*   Performs customization of said operating system

Glazier is no different. Glazier's Autobuild tool provides a means of
dynamically selecting the image(s), application(s), and configuration(s) to be
applied to a host. It retrieves any required files over the network, executes
scripts and binaries, and modifies the host as required.

Want to dive right in? See [here](doc/README.md) for further Glazier documentation.

## Why Glazier?

Glazier was created with the following 3 core principles in mind:

### Text-based & Code-driven

With Glazier, imaging is configured entirely via YAML files. This allows
engineers to leverage source control systems to maintain and develop their
imaging platform. By keeping imaging configs in source control, we gain peer
review, change history, rollback/forward, and all the other benefits normally
reserved for writing code.

Reuse and templating allows for config sharing across multiple image types.

Configs can be consumed by unit tests, build simulators, and other helper
infrastructure to build a robust, automated imaging pipeline.

Source controlled text makes it easy to integrate configs across multiple
branches, making it easy to QA new changes before releasing them to the general
population.

### Scalability

Glazier distributes all data over HTTPS, which means you can use as simple or as
advanced of a distribution platform as you need. Run it from a simple free web
server or a large cloud-based CDN. HTTPS is a requirement.

Proxies make it easy to accelerate image deployment to remote sites.

### Extensibility

Glazier makes it simple to extend the installer by writing a bit of Python or
PowerShell code. See creating new actions under docs to get started.

Glazier's Actions are the core of the system's configuration language. Glazier
ships with some [existing actions](glazier/lib/actions/README.md), but for more
custom functionality, you can also create your own.

## Where do I start?

We recommend starting with [these docs](doc/README.md) to learn about how Glazier works under the hood.

## Contact

We'd love to hear from you! If you have any questions or suggestions regarding
the documentation below, please make a post in our public discussion list at
[glazier-discuss@googlegroups.com](https://groups.google.com/forum/#!forum/glazier-discuss).

If you have any general questions for the Windows Team at Google that wrote Glazier, please make a post in our public discussion list at
[google-winops@googlegroups.com](https://groups.google.com/forum/#!forum/google-winops).

## Disclaimer

This is not an official Google product.
