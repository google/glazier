# Glazier Build YAML Specification



Glazier uses YAML-based configuration files. These documents outline the
supported syntax.

    templates:
      software:
        include:
          - ['software/', 'build.yaml']
      some_template:
        manifest:
            - '#some_executable.exe'
        pull:
            ['somefile.txt', 'C:\somefile.txt']
    controls:
      - pin:
          'os_code': ['win2008-x64-se', 'win2008-x64-ee']
        template:
          - software
      - pin:
          'os_code': ['win7']
        template:
          - some_template

## Top Level

The top level is a dictionary of two elements, *templates* and *controls*.

### Templates

tl;dr Think of templates as function declarations.

Templates is a dictionary of named elements. The name is used to reference each
template from one or more control elements. Templates are not executed unless
referenced by a control element. Their primary purpose is to allow a logical
grouping of commands which may be recycled more than once to simplify the
overall configuration.

The second template level is the template name. Names can be arbitrary, but
ideally should have some relevance to what the template is doing.

Beneath the template name is the common command element structure described
below. Pins are not used in templates, as it is assumed they will be called from
a pinned control instead.

Example:

```yaml
templates:
  install-oregon-trail:  # <-- Template name
    Execute: [           # <-- glazier Action
        ['googet install -noconfirm oregon-trail']
    ]
    Reboot: []          # <-- glazier Action
```

### Controls

Controls is an ordered list of unnamed elements. The list structure is used to
provide a consistent ordering of elements from top to bottom, so commands can be
executed in a predictable order. All build yamls execute commands from top to
bottom.

The second control level is the common command structure detailed below. A
control commonly starts with a pin item, unlike templates, but a pin is not
required. Unpinned controls will match all.

## Command Elements

Each individual block of the controls list or the templates dictionary can
contain any combination of the following, except for pins, which are exclusive
to control elements.

The order in which individual elements within a single command group are
processed is determined by the build code and may be subject to change. If you
need to control the order of operations, split the commands between multiple
command groups, as the groups are always process sequentially.

### Actions

Actions are dynamic command elements. Unlike the static commands listed on this
page, actions are not hardcoded into the config handler. When a configuration
file references a command that is not one of the known static commands, the
config handler will attempt to look up the class name in the actions module. If
it finds it, the class is loaded and run with the arguments from the
configuration file entry.

Actions are the preferred method for adding new functionality to the autobuild
tool. Unlike hardcoded commands, actions are almost fully self contained and
capable of self-validating.

See [the Actions README](../../glazier/lib/actions/README.md) for a list of available
actions.

### Pin

Exclusive to control elements, the pin attaches the current block to a specific
set of build info tags. The tags are inclusive, and must *all *match in order
for the command block to be executed by the build. The format is a dictionary,
where the key is the variable name from buildinfo and the value is a list of
acceptable values. If the key value in buildinfo matches any of the strings in
the list, the pin passes for that key.

Some pins support "loose" matching. In the case of loose matches, the entire pin
string is checked against the start of every corresponding buildinfo value. For
example: 'A-B' matches 'A-B' as well as 'A-B-C-D', but not 'A-C'.

    - pin:
        'os_code': ['win7']
        'department': ['demo']

Inverse pinning is also supported. Inverse pins are like regular pins, with the
match string beginning with an exclamation point (!). An inverse pin returns
False if any one buildinfo value matches the inverse string (minus the !). For
example: `'os_code': ['!win7']` excludes the pin from os_code=win7 hosts.

While direct match pins are exclusive, skipping any values not named in the set,
inverse match pins are inclusive, accepting any values not named directly. If
the pin is not negated by a matching inverse pin, the outcome is a successful
match. For example: `'os_code': ['!win7', '!win8']` is False for os_code=win7
and False for os_code=win8, but True for os_code=win2012.

*Direct pins are only considered if no inverse pins are present.* This is to
compensate for direct matches being exclusive in nature. It would not make sense
to supply \[!A, !B, C\], because \[C\] would have the same result.

Pins are generally treated as case insensitive.

### Policy

The policy tag specifies an imaging policy. Imaging policies are used to verify
that the state of the host being installed meets a given set of expectations.

Each policy tag element is a single string consisting of the name of the imaging
policy class to be enforced. The class name must match exactly, as classes are
dynamically referenced.

    - policy:
        - 'DeviceModel'

See also [the Policies README](../../glazier/lib/policies/README.md)

### Template

The template tag tells build to process a list of one or more named templates.
Templates are processed recursively, so templates can call other templates as
well.

    template:
          - workstation

### Include

The include tag tells build to process an additional yaml file. The structure is
a list of two part entries, a directory name relative to the current build
directory, and a build file name. Includes are useful for breaking up large
build files into smaller logical groups.

    include:
          - ['demo/', 'build.yaml']

## Supported Pins

The pins are essentially exported build info variables that help identify the
installing host. Not all of build info is exported for the purposes of pinning,
although it's always possible to extend the code to support different pins in
the future.

*   computer_model
    *   The computer model hardware string (eg HP Z620 Workstation)
    *   Supports partial model matching from the left.
*   device_id
    *   A hardware device id string in the format of
        \[vendor-device-subsystem-revision\]. Will be matched against every
        device id detected in hardware.
    *   Supports partial device matching from the left (eg AA-BB in the config
        will match AA-BB-CC-DD in hardware).
*   encryption_type
    *   tpm, none
*   graphics
    *   Detected graphics cards (by name).
*   os_code
    *   Corresponds to the generic operating system code as defined in
        release-info.yaml. Used for generalized identification of the target
        platform.

## Misc

### Comments

The yaml specification allows comments by prefacing lines with a hash (#). Feel
free to comment the configs to improve readability.

## Configuration Handlers

See the [Glazier Configuration Handlers](../setup/config_handlers.md) page for more
information about how the configuration files are processed.
