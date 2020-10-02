# Glazier

| Support | Python Tests | Contributing | Open Issues | License |
| ------- | ------------ | ------------ | ----------- | ------- |
[![Google Groups - Glazier](https://img.shields.io/badge/Support-Google%20Groups-blue)](https://groups.google.com/forum/#!forum/glazier-discuss) | [![Python Tests](https://github.com/google/glazier/workflows/Python%20Tests/badge.svg)](https://github.com/google/glazier/actions?query=workflow%3A%22Python+Tests%22) | [![Contributing](https://img.shields.io/badge/contributions-welcome-brightgreen)](https://github.com/google/glazier/blob/master/CONTRIBUTING.md) | [![Open Issues](https://img.shields.io/github/issues/google/glazier)](https://github.com/google/glazier/issues) | [![License](https://img.shields.io/badge/License-Apache%202.0-orange.svg)](https://github.com/google/glazier/blob/master/LICENSE)

[Gla·zier](https://en.wikipedia.org/wiki/Glazier) /ˈɡlāZHər/ *noun*: a person who installs windows.

Glazier is a tool developed at Google for automating Windows operating system deployments.

### How it works

*   Boots a system into the Windows Preinstallation Environment (WinPE)
*   Reaches out to a web server for instructions over HTTPS
*   Applies a base operating system
*   Installs applications and configurations to said operating system

Want to dive right in? See [here](doc) for documentation on how you can get started with Glazier in your environment.

## Why Glazier?

Glazier was created with the following 3 core principles in mind:

### Text-Based & Code-Driven

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
ships with some [existing actions](glazier/lib/actions), but for more
custom functionality, you can also create your own.

## Getting started

See our [setup docs](doc/setup) to learn about how you can get started with Glazier in your own environment.

## Contact

We'd love to hear from you! If you have any questions or suggestions regarding
the documentation below, please make a post in our public discussion list at
[glazier-discuss@googlegroups.com](https://groups.google.com/forum/#!forum/glazier-discuss).

If you have any general questions for the Windows Team at Google that wrote Glazier, please make a post in our public discussion list at
[google-winops@googlegroups.com](https://groups.google.com/forum/#!forum/google-winops).

## Disclaimer

Glazier is maintained by a small team at Google. Support for this repo is treated as best effort, and issues will be responded to as engineering time permits.

This is not an official Google product.
