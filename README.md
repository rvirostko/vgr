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

```bash
pip install vgr
```

<!-- Or, if not yet published to PyPI: -->

```bash
git clone https://github.com/rvirostko/vgr.git
cd vgr
pip install -e .
```

## Quick Start

The install can be tested using a simple script on the
command line.

```bash
vgr --execute "Print 'Hello, world'"
```

> Note:
> The first run will take some extra time as VGR builds out and caches
> internal data. Subsequent start-up times will be shorter.

See [`samples/`](./samples) for more complete examples.

Run `vgr` without argument to enter the REPL.

## Documentation

A full language reference in Markdown can be produced by using

```bash
vgr --gen-doc
```

This information is available from inside the REPL by using `help`
at the prompt. Use `Exit` to exit the REPL.

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
run-tests
```

A coverage file which can be used with VSC is produced.

<!-- Add coverage invocation, markers, or any harness-specific notes here. -->

### Building

```bash
scripts/mk-dist
```

This will create the dist directory for a wheel file and a zip file
of the samples. It will also contains an installer file, install-vgr.

### Utilities

These utilities live in [`scripts/`](./scripts).

#### `bump-version`

Modifies source artifacts to set the version and release date. Takes a
single argument:

- `major` : increments the major version, clearing minor and rev, and sets the date
- `minor` : increments the minor version, clearing rev, and sets the date
- `rev` : increments the revision and sets the date
- `date` : sets only the release date

#### `clean`

Cleans up the development environment. Removes logs, test results, and
other generated artifacts.

#### `dump-commits.py`

Generates a text file used in preparation of release notes / `CHANGELOG.md`
entries.

#### `vgr-debug` and `watch-debug`

Work together via a FIFO where VGR's stderr is redirected. Run them in
separate windows, in any order. `Debug` is not started automatically; enable
it with `--debug` on the `vgr-debug` command line, or from inside a script
or the REPL.

## Changelog

See [`CHANGELOG.md`](./CHANGELOG.md) for release history.

## Contributing

See [`CONTRIBUTING.md`](./CONTRIBUTING.md) for how to propose changes, code
style expectations, and the release process.

## License

VGR is released under the [Hippocratic License 3.0](./LICENSE.md) — an
ethical-source license, not OSI-approved. See `LICENSE.md` for full terms.

[![Hippocratic License HL3-BDS-CL-ECO-EXTR-FFD-LAW-MEDIA-MIL-MY-SOC-SV-TAL-XUAR](https://img.shields.io/static/v1?label=Hippocratic%20License&message=HL3-BDS-CL-ECO-EXTR-FFD-LAW-MEDIA-MIL-MY-SOC-SV-TAL-XUAR&labelColor=5e2751&color=bc8c3d)](https://firstdonoharm.dev/version/3/0/bds-cl-eco-extr-ffd-law-media-mil-my-soc-sv-tal-xuar.html)
