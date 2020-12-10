# Tips for Writing Effective Glazier Configs

*   YAML supports comments. Use them to delineate/decorate config blocks as well
    as communicating intent or documenting bugs/TODOs.
*   Some parts of configs are strictly ordered and others are not. The
    top-level, implemented as an ordered list, will always happen in sequence.
    Be careful not to assume strict ordering in other parts of the config,
    particularly where the YAML is dictionary typed. When in doubt, use two
    top-level config elements to assert order of operations.
    *   You can also achieve ordering with list-based types, such as templates
        and includes.
*   Use includes to combine a series of commands all affected by the same Pins.
    Rather than applying the same Pins to each of a series of configs, put the
    entire series in a separate file. Then apply the shared Pin(s) to the
    include statement that references the new config file.
*   Use includes and directory structure to break up the configuration flow in a
    logical way. Everything could live in one file and directory if you wanted
    it to, but it would be ugly and hard to read.
*   It's easier to cherrypick changes from separate files. Consider separating
    elements that are frequently changed for easier management across branches.
