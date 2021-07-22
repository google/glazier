# Glazier: Registry Package

<!--* freshness: { exempt: true } *-->

The Glazier registry package provides helper functions for simplifying common
interactions with the Windows registry.

Most of the registry helpers here are self contained and work well for basic use
cases (one-off reads/writes). The helpers are less ideal for complex uses,
particularly in instances where multiple registry operations have to be run in
rapid succession, or where performance is a concern. In those situations, it's
preferred to use the underlying registry library directly, which allows registry
handles to be held on and reused.
