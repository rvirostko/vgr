# Contributing to VGR

## Project Status

VGR is under active, single-maintainer development. **This project is not
currently accepting external pull requests or unsolicited contributions.**
This may change in the future as the language stabilizes

This document will be updated if/when that happens.

## Reporting Bugs

Bug reports *are* welcome. Before filing one:

- Search [existing issues](https://github.com/rvirostko/vgr/issues) to
  avoid duplicates.
- Confirm the behavior against the current `main` branch.

When filing, please include:

- VGR version (`vgr --version`) and Python version
- A minimal `.vgr` script that reproduces the issue
- Expected vs. actual behavior
- Full error output / traceback, if applicable

## Feature Requests / Discussion

Feature requests and design discussion are welcome as issues, but should
not be accompanied by a pull request implementing them — see
[Project Status](#project-status) above. Framing a request around the
problem you're trying to solve, rather than a specific syntax proposal,
is more useful at this stage of the language's design.

## Development Setup

See [`README.md`](./README.md#development-environment) for environment
setup, testing, and build instructions.

## Code Style

- Linting is enforced via [`.pylintrc`](./.pylintrc); run `pylint` before
  submitting any patch (see note above re: current PR policy).
- Markdown is linted via [`.markdownlint.jsonc`](./.markdownlint.jsonc).

## Release Process

See [`CHANGELOG.md`](./CHANGELOG.md) and the `bump-version` utility
described in [`README.md`](./README.md#bump-version).

## License

By reporting issues or otherwise interacting with this project, you agree
your contributions are subject to the terms in
[`LICENSE.md`](./LICENSE.md).
