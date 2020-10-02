# Chooser UI



The Chooser setup UI is an enhancement to autobuild which allows Glazier to
present the user with a dynamic list of options as part of the installation
process.

## Architecture

When the configuration handler code reaches a 'choice' option, that element is
stored in buildinfo as pending. The system will continue to accumulate pending
options until the config calls an action to display the UI.

The UI display action retrieves all collected options and passes them to a fresh
UI instance. The Chooser UI is responsible for presenting the options and
collecting any responses from the user.

The Chooser dynamically populates the visible UI from top to bottom. Each field
is contained in a frame, allowing the overall structure to flow downwards, even
though different fields may contain more or fewer individual elements. If the
user does not engage the UI, the responses are still populated using the default
selections.

![Chooser Frames](chooser_frames.png)

Once the UI exits, the Chooser will make the responses available via a
dictionary to the caller. The resulting "response" values are returned to
buildinfo where they will be saved in state. These same values (dynamically
named as USER\_\*) can be referenced via pinning at any point later on in the
build.

## Syntax

The Glazer YAML specification allows Chooser options to be encoded as part of
the build config files. Autobuild compiles and translates these options into an
option file for the chooser in stage15. Leveraging the build YAMLs allows for
all the same pinning and templating capabilities as the other commands, meaning
Chooser options can be targeted at images on the fly based on any available
buildinfo data.

The top level YAML command *choice* indicates a chooser option. Each choice
consists of several required sub-fields:

### name

Name designates the option's internal name, and should be unique. Buildinfo will
aggregate all options as USER_\[name\] where name is determined by this field.

### type

Type indicates the UI field type to be shown (see below).

### prompt

Prompt is the text label shown in the UI next to the interactive fields.

### options

An ordered list of dictionaries containing all options to be presented. Each
dictionary in the list should have the following sub-fields.

*   label: The label shown in the UI next to the selector.
*   value: The value to be stored in the backend if this option is chosen.
*   tip: Tooltip (currently not implemented)
*   default: Set to boolean True to indicate the default selection. The field
    can be skipped for all non-defaults.

## Field Types

### radio_menu

The radio_menu field provides a multiple choice drop-down menu. The menu allows
one and only one selection at a time from the available options.

    choice:
              name: system_locale
              type: radio_menu
              prompt: 'System Locale'
              options: [
                    {label: 'de-de', value: 'de-de', tip: ''},
                    {label: 'en-gb', value: 'en-gb', tip: ''},
                    {label: 'en-us', value: 'en-us', tip: '', default: True},
            ...
        ]

### toggle

A simple pair of on/off (or true/false) radio buttons.

        choice:
              name: puppet_enable
              type: toggle
              prompt: 'Enable Puppet'
              options: [
                    {label: 'False', value: False, tip: '', default: True},
                    {label: 'True', value: True, tip: ''},
              ]
