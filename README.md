# VGR - A Scripting Language

VGR is a scripting language designed around the following principles

- *Linguistic Alignment* with English and other programming languages
- *Polymorphic* and *Error Tolerant* operations
- *Interchangeable operator syntax* including
  - ASCII symbols - e.g. `+`, `<=`, `!=`
  - Unicode typographic equivalents - e.g. `≤`, `≠`, `∈`
  - English phrase forms - e.g. `Is Less Than`, `Is Not`
  - Standalone statements -  e.g. `Add`, `Subtract`,
    `Multiply`, and `Divide`
  - Stand-alone functions - e.g. `Mul(Add(x, y), z)`
  - Expressions as *transformative pipelines* - e.g. `x.Add(y).Mul(z)`
- *Solve more problems than you create* - Language features should
  strive to solve problems and avoid creating new ones
- *If it hasn’t been tested, it doesn’t work* - As features are developed
  they should be tested and code coverage should be as complete as possible

## Table of Contents

- [VGR - A Scripting Language](#vgr---a-scripting-language)
  - [Table of Contents](#table-of-contents)
  - [Installation](#installation)
  - [Quick Start](#quick-start)
  - [Documentation](#documentation)
  - [Development Environment](#development-environment)
    - [Set-up](#set-up)
    - [Testing](#testing)
    - [Building](#building)
    - [Utilities](#utilities)
      - [`bump-version`](#bump-version)
      - [`clean`](#clean)
      - [`dump-commits.py`](#dump-commitspy)
      - [`vgr-debug` and `watch-debug`](#vgr-debug-and-watch-debug)
  - [Changelog](#changelog)
  - [Contributing](#contributing)
  - [License](#license)

## Installation

Download a [release](https://github.com/rvirostko/vgr/releases) and
install the `whl` file.

```bash
pip install vgr-1.2.2-py3-none-any.whl
```

Alternately, clone the [repository](https://github.com/rvirostko/vgr.git)
and work from a development environment.

```bash
git clone https://github.com/rvirostko/vgr.git
cd vgr
source scripts/setup
```

## Quick Start

The install can be tested using a simple script on the
command line.

```bash
vgr --execute "Print 'Hello, world'"
```

> **Note**
>
> The first run will take some extra time as caches
> and internal data are built out.
> Subsequent start-up times will be shorter.

See [`samples/`](./samples/README.md) for more complete examples.

Run `vgr` without argument to enter the REPL.  Use `Exit` to exit the REPL.

## Documentation

A full language reference in Markdown is available as part
of each [release](https://github.com/rvirostko/vgr/releases).

This information is available from inside the REPL by using `help`
at the prompt. It is also availble inside Visual Studio Code when the VGR Language extension has been installed.

## Development Environment

Development scripts live in [`scripts/`](./scripts).

### Set-up

```bash
git clone https://github.com/rvirostko/vgr.git
cd vgr
source scripts/dev-setup
```

The script sets up a virtual environment and configures the path to
search the scripts directory automatically. Additionally it sets
`VGR_PATH` to search the samples and test scripts directory.

### Testing

```bash
scripts/test
```

An XML coverage file which can be used with Visual Studio Code is produced. To produce a coverage file as a set of HTML files
use:

```bash
scripts/test --cov-report=html
```

### Building

```bash
scripts/build
```

This will create the dist directory for a wheel file and a zip file
of the samples.

### Utilities

These utilities live in [`scripts/`](./scripts).

#### `bump-version`

Modifies source artifacts to set the version and release date. Takes a single argument:

- `major` : increments the major version, clearing minor and rev, and sets the date
- `minor` : increments the minor version, clearing rev, and sets the date
- `rev` : increments the revision and sets the date
- `date` : sets only the release date

#### `clean`

Cleans up the development environment. Removes logs, test results,
and other generated artifacts.

#### `vgr-debug` and `watch-debug`

These work together via a FIFO, redirecting VGR's stderr there. Run them in
separate windows, in any order. Note that `Debug` is not started automatically; enable
it with `--debug` on the `vgr-debug` command line, or from inside a script
or the REPL. You can also these to observe the results of `--verbose` and
`--echo`, as all options send their output to stderr.

## Changelog

See [`CHANGELOG.md`](./CHANGELOG.md) for release history.

## Contributing

See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for how to propose changes, code
style expectations, and the release process.

## License

VGR is released under the [Hippocratic License 3.0](./LICENSE.md) — an
ethical-source license, not OSI-approved. See `LICENSE.md` for full terms.

[![Hippocratic License HL3-BDS-CL-ECO-EXTR-FFD-LAW-MEDIA-MIL-MY-SOC-SV-TAL-XUAR](https://img.shields.io/static/v1?label=Hippocratic%20License&message=HL3-BDS-CL-ECO-EXTR-FFD-LAW-MEDIA-MIL-MY-SOC-SV-TAL-XUAR&labelColor=5e2751&color=bc8c3d)](https://firstdonoharm.dev/version/3/0/bds-cl-eco-extr-ffd-law-media-mil-my-soc-sv-tal-xuar.html)
