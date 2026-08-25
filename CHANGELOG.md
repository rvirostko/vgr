<!-- markdownlint-disable MD024 -->

# VGR Changelog

## [Unreleased]

### Added

- Added "GetFileInfo()" to retrieve information on one or more file/directory paths.
  Variable length arguments and supports polymorphism with lists and dictionaries.
- Added "Head()" and "Tail()" to return a subset of lists.
- Added "RandomSample()" which returns a subset using either a percentage
  or count of items.

### Changed

- Breaking change: Left/RightShift() renamed to ShiftLeft/Right()
  to match RotateLeft/Right()
- Breaking change: Include/Exclude Nulls removed from Select For Text. They
  we inherited from JSON output, but made no sense here.
- Breaking change: Select For Text headers now works more like CSV output
  rather than JSON.
- Breaking change: IsTitle() renamed to IsTitleCase() to match the
  TitleCase() operation.
- Constant statement can now create a constant from an initialized variable
  without having to use an assignment (e.g. "Set x To 5; Constant x").
  Additionally, this form of the statement is idempotent.
- "load-from-test" updated with newer syntax
- The "Paths" option of Create-Zip now has an optional leading "Keep",
  so you either "Keep Paths" or "Junk Paths"
- The following string functions now support variable arguments:
  Capitalize(), CaseFold(), Chr(), IsAlpha(), IsAlphaNumeric(), IsAscii(),
  IsDecimal(), IsDigit(), IsLower(), IsNumeric(), IsPrintable(),
  IsSpace(), IsTitleCase(), IsUpper(), Lower(), Ord(), ReverseStr(),
  StringLen(), SwapCase(), TitleCase(), Upper()
- The following string functions now support variable arguments:
  ExpandTabs(), LeftStr(), RightStr(). When given multiple arguments,
  the final one is checked to see if it is None or a numeric value.
  If so, it is used for the length/size value rather than one of the
  inputs to be transformed.
- The following general purpose functions now support variable arguments:
  Clone(), Hash(), Id(), IsFalse(), IsTrue(), Length(), Negate(),
  Repr(), Reverse().
- DefaultTo() now takes multiple default values, returning the first
  non-None one.
- Internal change: automatic registration of built-in functions

### Deprecated

### Removed

- GetKeyValue() and other dictionary functions had an undocumented behavior
  of using a dotted path to traverse levels. This made it impossible to
  retrieve valid keys that contained periods. This behavior has been removed.
  If you need this type of behavior, use a list for the path, as each
  element is a single step.
- Ascii() has been removed; use Repr() instead
- math.random and math.random100 removed. They predated the ability to
  have functions with zero args, and both are replaced by Random().
- math.inf, math.nan, and math.neg_inf have been removed as they were all
  replaced with figurative constants a while ago

### Fixed

- Vault calls broken by "HttpResponse object has no attribute url"
- Http returns url and request_url as strings rather than URL instances
- RightStr(0) returned entire string when result should have been
  an empty string.
- Escaping of typographic quotes in strings no longer causes an error

### Security

## [1.2.1] - 2026-08-06

### Added

- Added the "Abort" statement, which is an unconditional error exit,
  but unlike "Assert" does not require a test to pass/fail.
- Vault response now includes the namespace passed in the request
- Vault client logged messages now include the connection name.
  The name also appears in the Vault response.
- Vault connection errors go to the log
- Added Vault operation aliases for "Read" (GET) as well as
  "Create" and "Update" (POST)
- Logging supports the Critical level
- Log Level accepts Off to disable logging
- Clarified what "--loglevel" does, which is configure the root logger
- vgr.log.file now contains the name of the logging file
- Added generated github issue templates
- Added basic CONTRIBUTING.md
- Backfilled this change log from tags

### Changed

- Clean up of test output: ignore unfixed error in ldap3 that generates
  a deprecated error message, add a way to add "xfail" to script testing
  so we can be smarter about external systems, or WIP samples.
- Improved README.md, focusing on new users and devlopment
- vgr.log_level has be changed to vgr.log.level.
  It is also populated at start-up (previously undefined)
- Exhibit displays additional information about variables when
  Verbose mode is on

### Removed

- Unimplemented Pure modifier for Function removed

### Fixed

- Speculative fix for ^C breaking REPL in Windows
- Fix the "in-tree-build" issue by making sure we have a version of pip that
  no longer requires the option. We'll automatically upgrade to 23.0 if we need to.
- Fix for raw strings parse error when the last character is a
  backslash.
- Fix documentation for Vault List, Get, Post et al commands
- Fix regression with echo on/off (but not no-args or expr) echoing itself.
- Fix for documentation missing for Is Defined, Is Empty, Is Constant and
  their negated versions.
- Accept Input's "To" was not case insensitive
- Accept Input lacked hyphenated version
- Errors in Log Level value point to the level not the start of the statement
- --logoverwrite behavior was backwards (acting like append)
- In the REPL, the exit code from "Exit" was not propogated to the shell
- Abort and Assert statements no longer cause the REPL to exit
- Fix end point used to work with Vault static LDAP roles
  (now "static-role", previous "static-cred")
- Fix bug in fib.vgr sample and remove unneeded code
- Exhibit uses proper terminolgy for undefined variables

## [1.2.0] - 2026-07-13

### Added

- "End-type" block closures introduced as preferred way to close
  blocks, reducing reliance on : and ; in grammar
- "HTTP" statement added for curl-like operations
- New "Constant" statement for declaring immutable values.
  Also available as a modifier for "Define Function".
  "Reset" can be used to remove all constants.
- Subscript notation--[...]--now works in an expression on lists, dictionaries,
  and strings, dispatching to Item()/GetKeyValue()/SubStr() internally
- Negative indexing: Item() and SubStr() support negative indices
  consistently. Out-of-bounds errors return None.
- Regex literals: new "r/.../[flags]" inline syntax. Additionaly,
  CompilePattern() accepts the same flags as a string.
- ExtractMatch()/ExtractMatches() regex functions added
- "re.pattern" variable added: a built-in dictionary common patterns
- Random()/RandomChoice() added
- New operators: Is Defined/Is Undefined, Is Empty/Is Not Empty
- Substantial expansion of date-time functions
- Encoding options added to "Open", "Sort", and "Load" allowing for
  consistent syntax across statements
- "Select" enhancements: "Cartesian product" clause fully operational,
  "Into" clause (file/stream/variable output) added,
  and "Select *" supported
- "Constant" function modifier added; other function modifiers
  ("Pure" and "Cached") parse but error as unimplemented

### Changed

- "Terminal" statement had a major breaking revision reducing keyword count
- In "Select" statements, $rowid renamed $rec-index
- "ForEach" statment is now "For Each" or "For-Each"
- "Set" statement is now required - no more C-like bare assignment
- "Declare" statments requires commas between variables
- "Print/Printf" statments channel options ("To output", "As Markdown")
  moved to the end of the statement with "To/As" now required
- "Print" statement new "OFS/Field Separator" and "ORS/Record Separator"
  options added to augment AWK-like environment variable overrides
- "Printf" statement new "Flush" (default) and "No-Flush" options
- For all CSV outputs "Quoting" renamed to "Quoting Style"
- Arrow functions are created using "Define Function" instead of "Set"
- "Sort" statement: "Variable" and "Into" syntax removed; use "Giving"
- "Variable" modifier removed generally - use "File" for argument
  disambiguation
- Typo fix: "seperator" correctly renamed "separator" in keywords
- In "LDAP" statments "Time Limit" renamed "Timeout"
- "Contains Any" statement renamed "Contains". Additionaly, "Match/Contains"
  operators and functional forms lose their "Any" variants
- FileExists() renamed PathExists()
- IndexOf() no longer works with dictionary keys - use Contains() or "Is In"
- Format() with a list argument now returns a list
- In FormatJson() sorting defaults to False (was True), and indent is
  restricted to None or 0-32
- FormatJsonStr() removed as redundant
- In "Select" statment  encodings removed from output-type options;
  limit/offset handling simplified, and includes differing behavior on
  input vs. output counts
- Also in "Select": None records no longer auto-skipped; dictionly
  iteration now surfaces records as dictionaries, not lists
- Boolean truthy handling: single-letter boolean string variants
  (T/F etc.) removed and are now truthy regardless of their value
- "Reset" with no arguments acts like "Reset All", rather than a NOP
- Internally, regex patterns are a first-class type, with support across
  operators, string functions, and inequality comparisons. Typically, they
  are converted to strings when operations on the compiled
  pattern has no function.
- RSplit(), RIndexOf(), IndexOf(), Split(), CountOf(), Strip() support
  patterns and collections uniformly
- Multiple assignment: "Set" and "Assign" can now assign several
  variables in one statement, separating assignments with commas
- "Choose" statement improvements: supports "Matches/Is In",
  undefined-variable testing. Colons in statements now optional
- VS Code extension: TextMate grammar improvements, keyword boundary
  fixes, debugging support, icon/branding

### Removed

- BASIC/COBOL extension purge:
  - "Do" statements (Forever/Until/While) and typed "Exit/Continue" removed
  - "Perform Varying", "Perform Until", "Perform-Times", "Exit Perform Cycle",
    "Exit Program", "Stop Run", "Compute", "Evaluate", "Display",
    and "String" statements removed
  - Typed "Break" loop-exit syntax removed
  - "Tron/Troff" removed; use "Echo" instead
  - COBOL aliases for stdin/stdout removed
  - "Let" statement removed
- Single-letter modes used when opening files ("r", "w", "a") removed
- "IMatch" operators removed - use a regex literal or CompilePattern()
- Special SetVar() function removed - use function with side effects instead

### Fixed

- List and dictionary constants in "Select" got empty default labels
- "Choose" failed when there was no "When" or "Otherwise" clause
- Modulo by zero now matches division, returning nan
- "Select" text output ignored option settings
- "Sort"'s ascending/descending option wasn't working correctly
- Boolean-handling bug in "Exit"; now works as described

## [1.1.10] - 2026-03-03

### Added

- Added an installer script
- "Perform n Time" now allowed for linguistic alignment
- Added COBOL compatible "Exit Perform" as well as "Exit Program"/"Goback"
- Added "Is Positive" and "Is Negative" operators and functions
- Added "Is Even" and "Is Odd" operator and functions

### Changed

- De-tuple-ization
- Improved error output
- Old readme now part of documentation
- Improved dev-setup so you can get to work faster
- Old embeded REPL help now in doc files
- Refactor redirector code and provide a way to know if stdin is available
- Samples are now run as part of test to make sure they are up-to-date
- Many functions are now 0..n args so they are more forgiving of errors
- Exit/Continue block now enforce the check on the block type
- "End" allowed to close For loops for linguistic alignment
- Updated VGR syntax coloration for some missing keywords
- Variable names cannot end with "-" to better aid parsing
- Lots of internal renaming of modules and a few functions (see new "builtins")
- The capabilities of "Load" are now exposed as a set of functions which it uses
  to parse the data read from a file (See ParseJSON et al). Note that "Select"
  and "Sort" also are layered on these functions.

### Removed

- Strlen() and Strrev() alias removed
- Incorrect "Do" and "By" syntax removed in multiple places

### Fixed

- Markdown fixes for improper emphasis/strong usage
- Doc fix: use VGR types not Python's
- Bug fix: functions with 0..1 args had improper signature calculation
- Bug fix: Break/Continue were incorrectly allowed in Choose
- REPL actually uses "Exit" rather than doing special checks, which
  caused weird results with "Exit Do" et al

## [1.1.9] - 2026-02-10

### Added

- Auto generated documentation

### Changed

- Enhancements to Load

## [1.1.8] - 2025-11-25

### Added

- Added LOTS of advanced bit operations.

### Changed

- Dictionary and list functions: GetValues(), Apply(),
  CombineUsing(), Dict().
- CombineWith() renamed CombineLists().

## [1.1.7] - 2025-11-17

### Changed

- Addition of list and dict functions.
- Clean up of imports across mods.
- Replace type_str with direct poly_type call.
- Allow calling of user funcs from mathpak functions.

## [1.1.6] - 2025-10-27

### Fixed

- Syntax warning for escape seq in 3.12
- Ldap Connect fails with NTLM ("NTLM" works)
- Ldap Disconnect with name fails

### Changed

- Improved naming of test log files for statements

## [1.1.5] - 2025-10-24

### Added

- Added "with no advancing" to Display statement
- Added "no echo" and "secure" to Accept statement
- Added "String" statement
- Added "figurative constants" for Space, Zero, and Quote

### Changed

- Move to "Is" instead of "=/Is" for option settings (breaking change)
- Certain consts (none, true, false) are no longer excluded
  from variable names

### Fixed

- FormatJson() errors
- Alias problem with immutable prefixes
- Problems with using backslash in strings for paths
- Repr() error in strings that start and end with quotes
- LDAP argument parsing errors

## [1.1.4] - 2025-10-21

Lots of documentation and bug fixes.
Work on the Vault extn and a release
candidate of the LDAP extn.
Command line changes to be more AWK-like
which included the addition of the @include
statement and VGRPATH so we can create
libraries.

## [1.1.3] - 2025-09-30

Mostly work on documentation and
presentation of same in help.
All the string related functions
have been checked and documented.

## [1.1.2] - 2025-09-26

Fixes for Windows and newer
revs of Python.

[Unreleased]: https://github.com/rvirostko/vgr/compare/v1.2.1...HEAD
[1.2.1]: https://github.com/rvirostko/vgr/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/rvirostko/vgr/compare/v1.1.10...v1.2.0
[1.1.10]: https://github.com/rvirostko/vgr/compare/v1.1.9...v1.1.10
[1.1.9]: https://github.com/rvirostko/vgr/compare/v1.1.8...v1.1.9
[1.1.8]: https://github.com/rvirostko/vgr/compare/v1.1.7...v1.1.8
[1.1.7]: https://github.com/rvirostko/vgr/compare/v1.1.6...v1.1.7
[1.1.6]: https://github.com/rvirostko/vgr/compare/v1.1.5...v1.1.6
[1.1.5]: https://github.com/rvirostko/vgr/compare/v1.1.4...v1.1.5
[1.1.4]: https://github.com/rvirostko/vgr/compare/v1.1.3...v1.1.4
[1.1.3]: https://github.com/rvirostko/vgr/compare/v1.1.2...v1.1.3
[1.1.2]: https://github.com/rvirostko/vgr/releases/tag/v1.1.2
