# NAMEs are generally "snake case", "kabab case", and mixed version of the two, with some limitations.
# For "kabab", it cannot start with a hyphen and an alpha character must follow a hyphen.
# This is an attempt to prevent some subtraction operations from looking like identifiers
#
# The following characters are permitted:
#     * '$' in the first position only
#     * '_'
#     * Latin characters (A-Z, a-z, \u00C0-\u00FF, \u0100-\u017F, \u0180-\u024F, \u1E00-\u1EFF)
#     * ASCII digits (0-9) except for the first character
#     * Greek letters (\u0370-\u03FF)
#     * Mathematical alphanumeric symbols (\U0001D400-\U0001D7FF - supplementary plane / 32bit Unicode)
#     * Optional suffix of one or more prime indicators (\u2032), double thru quad prime indicators (\u2033, \u2034, \u2057),
#       or a single subscripted digit (\u2080-\u2089)
#
# NB: Lark uses the Python re module, which cannot handle Unicode character classes like \u1D400-\u1D7FF
#     in the standard way for supplementary characters unless the Python build fully supports UTF-32 internally.

#pylint: disable=line-too-long
VAR_NAME = r"[A-Za-z$_\u00C0-\u00FF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF\u0370-\u03FF\U0001D400-\U0001D7FF](?:[A-Za-z0-9_\u00C0-\u00FF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF\u0370-\u03FF\U0001D400-\U0001D7FF]|-+[A-Za-z\u00C0-\u00FF\u0100-\u017F\u0180-\u024F\u1E00-\u1EFF\u0370-\u03FF\U0001D400-\U0001D7FF])*(?:\u2032+|[\u2033\u2034\u2057\u2080-\u2089])?(?<!-)"
