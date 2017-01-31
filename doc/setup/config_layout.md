# Glazier Configuration Layout & Branches

This page discusses how Glazier's configuration files are laid out at the
distribution point (web server).

## About Branches

Branches are separate, independent configuration repositories.

The most common use of multiple branches is to have different levels of
stability: for example, a "stable" and "testing" branch of the same repository.
Changes are checked into the testing branch, and tested under controlled
conditions, before being copied over to the stable branch. In this way, broken
changes can be caught in testing without affecting end users.

You generally do not need multiple branches just to support different imaging
arrangements. A single branch can handle various types of hosts by pinning the
config elements.

## Components

The general layout of a Glazier config repository looks like this:

*   / (--config_server)
    *   version-info.yaml
    *   stable_branch/
        *   release-id.yaml
        *   release-info.yaml
        *   config/ (--config_root_path)
            *   build.yaml
    *   testing_branch/
        *   release-id.yaml
        *   release-info.yaml
        *   config/ (--config_root_path)
            *   build.yaml

### --config_server

The entire configuration is rooted at a web address supplied with
`--config_server`. For this example, we will assume glazier is hosted under,
https://glazier.example.com.

### version-info.yaml

The only configuration file that should exist under the very top level of the
config server is `version-info.yaml`.

This file's purpose is to match the host being imaged with a given branch.
Because branches are entirely self-contained repositories, we need some way to
instruct Glazier which branch to use. This allows the entire remainder of the
configuration to be isolated inside of the separate branches.

`version-info.yaml` contains a dictionary item *versions* whose contents are key
value pairs made up of the host's operating system name paired with the name of
a branch.

In this example, starting the build with `--glazier_spec_os=windows7-qa` will
load the config from the *testing_branch/* directory.

Example `version-info.yaml`:

    versions:
      windows7: 'stable_branch'
      windows7-qa: 'testing_branch'
      windows10: 'stable_branch'
      windows10-qa: 'testing_branch'

### branch/release-id.yaml

Each branch should contain a single `release-id.yaml` file. This file contains a
single dictionary key *release_id* with a value of your desired release
identifier. This gives each release a unique identification which will be saved
to the registry and logs for later inspection.

Example `release-id.yaml`:

        release_id: 1.2.3.4

### branch/release-info.yaml

The `release-info.yaml` contains various metadata about the state of the build.
This metadata is fed into the buildinfo library and supports various internal
behaviors. In a sense, it can be thought of as a configuration file for the
installer, which can be modified and deployed without any changes to the code
being required.

Example `release-info.yaml`:

    supported_models:
      tier1:
        [
          Windows Tier 1 Device,
          Another Tier 1 Device
        ]
      tier2:
        [
          Windows Tier 2 Device,  # Testing
        ]
    os_codes:
      windows7-qa:
        code: win7
      windows7-stable:
        code: win7
      windows10-qa:
        code: win10
      windows10-stable:
        code: win10

#### supported_models

*supported_models* enables the "support tiers" feature of the installer.
Enterprises may have different levels of device support and qualification. By
identifying models names as belonging to a given tier, administrators can
present different messages to users about whether or not a given host is known
and supported by the installer. The installer can present a warning for unknown
or deprecated devices with this feature.

#### os_codes

*os_codes* are tied to the `os_code` pin type used in the config files. This
feature allows the config files to use a generalized name for a given operating
system, when otherwise the same operating system might have multiple names.

In the example above, we have separate branches for QA
(`--glazier_spec_os=windows7-qa`) and stable
(`--glazier_spec_os=windows7-stable`). These are both Windows 7, and we want
Glazier to attempt to process the Windows 7 configuration in both cases. Rather
than having to apply both names, we generalize both to the code name *win7*. In
the config files, we can then do this:

      - pin:
          'os_code': ['win7']
        Execute:
          - [some_installer.exe]

Both branches QA and stable will then treat this command as belonging to the
Windows 7 install.
