# Glazier Documentation

We'd love to hear from you! If you have any questions or suggestions regarding
the documentation below, please make a post in our public discussion list at
[glazier-discuss@googlegroups.com](https://groups.google.com/forum/#!forum/glazier-discuss).

## Getting Started

See the links below to help get you started with your own Glazier configuration.

*   [About Glazier](./setup/about.md) - Basic operating principles used in
    Glazier.
*   [Setup Guide](./setup) - Getting started with the basic principles from the
    about page.

## Glazier Configurations

Glazier uses YAML-based configuration files. These documents outline the
supported syntax.

*   [Creating New Actions](./setup/new_actions.md) - Glazier's Actions are the
    core of the system's configuration language. Glazier ships with some
    existing actions, but for more custom functionality, you can also create
    your own.
*   [Glazier Config Layout](./setup/config_layout.md) - How Glazier's
    configuration files are laid out at the distribution point (web server).

## YAML Files

*   [Glazier YAML File Specs](./yaml) - Glazier uses YAML-based configuration
    files. These documents outline the supported syntax.
*   [Chooser Interface Configs](./yaml/chooser_ui.md) - The Chooser setup UI is
    an enhancement to autobuild which allows Glazier to present the user with a
    dynamic list of options as part of the installation process.
*   [Tips for Writing Effective Glazier Configs](./yaml/tips.md) - for writing
    your own Glazier YAML configuration files.

## Python

*   [Installer Actions](../glazier/lib/actions) - Actions are classes which the
    configuration handler may call to perform a variety of tasks during imaging.
*   [Policy Modules](../glazier/lib/policies) - Policy modules determine whether or not
    Autobuild should be allowed to proceed with an installation.
*   [Config Handlers](./setup/config_handlers.md) - The Glazier configuration
    handling libraries are responsible for taking the configuration language as
    input, determining which commands apply to the current system, and executing
    them as needed.
