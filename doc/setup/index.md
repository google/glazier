# Setup Guide

[TOC]

## Distribution

Glazier requires a web based repository of binary and image files to be
available over HTTP(S). You can use any web server or platform that suits your
needs.

Inside the root of your web host, create two directories: the config root and
the binary root.

### Config Root

The configuration root must contain at minimum one `build.yaml` file. In a
mature system, this directory will likely contain a variety of branching config
files and scripts.

We recommend keeping the entire contents of the config root in source control,
and exporting it out to the web service whenever changes are made.

### Binary Root

The binary root is a separate directory structure used to hold non-text data.
This split serves to draw a clean boundary between files which may be sourced
from version control, and those which may instead live in mass storage
elsewhere.

We recommend using an organized tree structure to make binaries easy to locate.

*   Root/
    *   Company1/
        *   Product1/
            *   v1/
            *   v2/
            *   ...
        *   Product2/
            *   v1/
        *   ...
    *   ...
