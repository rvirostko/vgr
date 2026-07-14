# VGR - A Scripting Language

[![Hippocratic License HL3-BDS-CL-ECO-EXTR-FFD-LAW-MEDIA-MIL-MY-SOC-SV-TAL-XUAR](https://img.shields.io/static/v1?label=Hippocratic%20License&message=HL3-BDS-CL-ECO-EXTR-FFD-LAW-MEDIA-MIL-MY-SOC-SV-TAL-XUAR&labelColor=5e2751&color=bc8c3d)](https://firstdonoharm.dev/version/3/0/bds-cl-eco-extr-ffd-law-media-mil-my-soc-sv-tal-xuar.html)

## Development Environment

** TODO **

### Set-up

** TODO **

### Testing

** TODO **

### Building

** TODO **

### Utilities

** TODO **

#### `bump-version`

Modifies source artifacts to set the version and release date. It takes
a single argument:

* `major` : increments the major version, clearing minor and rev,
  and sets the date
* `minor` : increments the minor version, clearing minor and
  sets the date
* `rev` : increments the revision and sets the data
* `date` : set only the release date

#### `clean`

Cleans up the development environment. Removes logs, test results, and
other artifacts that can be generated.

#### `dump-commits.py`

This utility generates a text file that is used in preparation
of release notes.

#### `vgr-debug` and `watch-debug`

This pair work with a FIFO where VGR's stderr is redirected.
You can run them—in separate windows—in any order.

Note that `Debug` is not started automatically; you can do that with `--debug`
on the `vgr-debug` command line or do it from inside a script or the REPL.
