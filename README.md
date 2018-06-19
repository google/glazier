# Glazier

Glazier is a tool for automating the installation of the Microsoft Windows
operating system on various device platforms.

Table of contents
=================

- [Glazier](#glazier)
  * [Why Glazier?](#why-glazier-)
  * [Contact](#contact)
  * [Disclaimer](#disclaimer)

## Why Glazier?

Glazier was created with certain principles in mind.

__Text-based & Code-driven__

With Glazier, imaging is configured entirely via text files. This allows
technicians to leverage source control systems to maintain and develop their
imaging platform. By keeping imaging configs in source control, we gain peer
review, change history, rollback/forward, and all the other benefits normally
reserved for writing code.

Reuse and templating allows for config sharing across multiple image types.

Configs can be consumed by unit tests, build simulators, and other helper
infrastructure to build a robust, automated imaging pipeline.

Source controlled text makes it easy to integrate configs across multiple
branches, making it easy to QA new changes before releasing them to the general
population.

__Scalability__

Glazier distributes all data over HTTPS, which means you can use as simple or as
advanced of a distribution platform as you need. Run it from a simple free web
server or a large cloud-based CDN.

Proxies make it easy to accelerate image deployment to remote sites.

__Extensible__

Glazier makes it simple to extend the installer by writing a bit of Python or
Powershell code.

## Contact

We have a public discussion list at
[glazier-discuss@googlegroups.com](https://groups.google.com/forum/#!forum/glazier-discuss)

## Disclaimer

This is not an official Google product.
