from typing import Callable
import re

from lark import Lark
from rich.console import Console, Theme
from rich.markdown import Markdown
from rich.syntax import Syntax

from pygments.lexer import RegexLexer
from pygments.style import Style
from pygments.styles import STYLE_MAP
from pygments.token import (
    Comment,
    Error,
    Escape,
    Generic,
    Keyword,
    Literal,
    Name,
    Number,
    Operator,
    Other,
    Punctuation,
    String,
    Text,
    Token,
    Whitespace,
)

_CODE_BG = "#f8f8f8"

_BASE_THEME = Theme({}, inherit=True)

_THEME = Theme({
    "markdown.text": "",  # Default terminal style
    # NB: Headings are all centered and look horrible: don't use
    #     until Markdown is fixed
    #     Also, __ul__ renders as bold
    # Foreground colors: standard names, 256-color, and hex
	# Background colors: on color
	# Text styles: bold, italic, underline, reverse, blink, dim, strike
    #"markdown.h1": "bold underline",
    #"markdown.h2": "bold",
    #"markdown.h3": "bold",
    #"markdown.h4": "bold",
    #"markdown.h5": "bold",
    #"markdown.h6": "bold",
    #"markdown.list": "",
    #"markdown.item": "",
    "markdown.block_quote": "",
    #"markdown.bold": "bold",
    #"markdown.italic": "italic",
    "markdown.code": str(_BASE_THEME.styles["markdown.item.bullet"]),
    "markdown.hr": "bold",
    "markdown.link": "underline",
    "markdown.image": "underline",
}, inherit=True)

_VGR_CODE_BLOCK_PATTERN = re.compile(r"```vgr\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)

class MdLexerState:
    lexer: "VgrLexer" = None

_STATE = MdLexerState()

def md_create_lexer(_parser: Lark) -> None:
    # TODO future : figure out how to get
    # dynamic values into that class: they
    # way that you think would work doesn't
    _STATE.lexer = VgrLexer()

_CONSOLE = Console(theme=_THEME)

def md_println(*args) -> None:
    """Prints one of more lines to the console as Markdown text"""
    console = _CONSOLE
    for arg in args:
        if arg is not None:
            s = str(arg)
            _blank_line(console) if s.isspace() else _print(console, s)

def _blank_line(console: Console): console.print("")

def _print(console: Console, s: str) -> None:
    """Handles the formatting of VGR code blocks"""
    last_pos = 0
    for match in _VGR_CODE_BLOCK_PATTERN.finditer(s):
        start, end = match.span()
        if start > last_pos:
            console.print(Markdown(s[last_pos:start]), sep=None, end=None)
        _print_code_block(console, match.group(1))
        last_pos = end
    # Add remaining text
    if last_pos < len(s):
        console.print(Markdown(s[last_pos:]), sep=None, end=None)

def _print_code_block(console: Console, code_block: str) -> None:
    """Write out a formatted VGR code block"""
    _blank_line(console) # outside blank line above
    console.print(Syntax(
        code=code_block.strip('\n'),
        lexer=_STATE.lexer,
        theme=VGRCodeStyle,
        line_numbers=False,
        padding=(1,2),
        background_color=_CODE_BG,
        tab_size=4,
        dedent=True
    ))
    _blank_line(console)  # outside blank line below

# Initially based on "default" style
class VGRCodeStyle(Style):
    background_color = _CODE_BG

    styles = {
        Text: "",
        Token: "",
        Escape: "",
        Literal: "",
        Other: "",
        Punctuation: "",
        Operator: "",

        Whitespace:                "#bbbbbb",
        Comment:                   "italic " + "#0a5301",
        Comment.Preproc:           "",

        Keyword:                   "bold " + "#6b0041",
        Keyword.Pseudo:            "nobold",
        Keyword.Type:              "nobold",

        Operator:                  "",
        Operator.Word:             "bold",

        Name.Builtin:              "italic",
        Name.Function:             "",
        Name.Class:                "bold",
        Name.Namespace:            "bold",
        Name.Exception:            "bold",
        Name.Variable:             "",
        Name.Constant:             "bold italic " + "#000000",
        Name.Label:                "",
        Name.Entity:               "bold",
        Name.Attribute:            "",
        Name.Tag:                  "",
        Name.Decorator:            "bold italic " + "#ff8051",

        String:                    "#2D0BF2",
        String.Doc:                "italic",
        String.Interpol:           "bold",
        String.Escape:             "bold " + "#000000",
        String.Regex:              "#2D0BF2",
        String.Symbol:             "#2D0BF2",
        String.Other:              "#2D0BF2",
        Number:                    "",

        Generic.Heading:           "bold",
        Generic.Subheading:        "bold",
        Generic.Deleted:           "",
        Generic.Inserted:          "",
        Generic.Error:             "",
        Generic.Emph:              "italic",
        Generic.Strong:            "bold",
        Generic.EmphStrong:        "bold italic",
        Generic.Prompt:            "bold",
        Generic.Output:            "",
        Generic.Traceback:         "",

        Error:                     "border:#FF0000"
    }

STYLE_MAP["vgr"] = f"{VGRCodeStyle.__module__}.{VGRCodeStyle.__qualname__}"

class VgrLexer(RegexLexer):
    name = "vgr"
    aliases = ["vgr"]
    tokens = {
        "root": [
            # Comments
            (r"//.*?$",    Comment.Single),   # double-slash
            (r"#.*?$",     Comment.Single),   # hash style
            (r"/\*.*?\*/", Comment.Multiline),

            (r" →( |$)", Name.Decorator), # This is used with functional output examples

            (r'\\(x[0-9A-Fa-f]{2}|u[0-9A-Fa-f]{4}|U[0-9A-Fa-f]{8}|N\{[^}]+\}|.)', String.Escape),

            # Single-quoted or double-quoted strings
            (r'[Rr]?("(?!"").*?(?<!\\)(\\\\)*?"|\'(?!\'\').*?(?<!\\)(\\\\)*?\')', String),
            # Triple-quoted strings (long strings, can be multi-line)
            (r'[Rr]?("""(.*?)(?<!\\)(\\\\)*?"""|\'\'\'(.*?)(?<!\\)(\\\\)*?\'\'\')', String),
            # Regular expressions
            # \x91 : [, \x92 : /, \x93 : ]
            (r"r/(?:(?:\x92[/\x92])|(?:\x91^/)|(?:\x91/)|(?:/\x93)|(?:[^\x00-\x1f\x7f/]))+/[adimsx]*", String.Regex),

            # Autogenerated with: python3 -m vgr --debug --gen-vsc-extn
            (r"(?i)(?<![.\w_])(:?RotateDbConnectionCredentials|GenerateDbRoleCredentials|RotateDbRoleCredentials|CreateDbConnection|DeleteDbConnection|UpdateDbConnection|CreateLdapLibrary|DeleteLdapLibrary|ListDbConnections|ListLdapLibraries|ResetDbConnection|UpdateLdapLibrary|DefaultNamespace|DeleteKvMetadata|MoveCursorToLine|ReadDbConnection|UndeleteKvSecret|CreateNamespace|DeleteNamespace|DestroyKvSecret|GetTerminalSize|MoveCursorToCol|ReadLdapLibrary|UnlockNamespace|UpdateNamespace|Authentication|CreateKvSecret|CreateLdapRole|DeleteKvSecret|DeleteLdapRole|ListNamespaces|ReadKvMetadata|RotateLdapRole|StrikeThruAttr|UpdateKvSecret|UpdateLdapRole|AlignmentTest|Call-Function|Corresponding|CursorForward|CursorVisible|DbConnections|LdapLibraries|ListKvSecrets|ListLdapRoles|LockNamespace|PatchKvSecret|ReadNamespace|RestoreCursor|SetBackground|SetForeground|UnderlineAttr|Accept-Input|ClearAllTabs|CreateDbRole|DbConnection|DeleteDbRole|End-Function|EraseDisplay|GetCursorPos|HTTP-Version|MoveCursorTo|ReadKvSecret|ReadLdapRole|ScrollRegion|SetClipboard|SmoothScroll|UpdateDbRole|ClearScreen|CreateMount|Credentials|DHighBottom|DeleteMount|Dereference|Description|ItalicsAttr|LdapLibrary|ListDbRoles|Operational|RaiseWindow|ReverseAttr|SetIconName|UpdateMount|Attributes|Connection|Create-Zip|CursorBack|CursorDown|DeleteChar|DeleteLine|Descending|Dictionary|Disconnect|DoubleWide|End-Choose|End-Repeat|End-Unless|HiddenAttr|HideCursor|HomeCursor|InsertChar|InsertLine|InsertMode|KvMetadata|ListMounts|Namespaces|OriginMode|Parameters|PrintDHigh|ReadDbRole|Remove-Key|RepeatChar|ResetAttrs|SaveCursor|ScrollDown|ShowCursor|SingleWide|Terminator|Ascending|BlinkAttr|BlockSize|Cartesian|Character|Constants|DeIconify|Delimiter|DrawHLine|DrawVLine|End-Until|End-While|EraseChar|EraseLine|HardReset|KvSecrets|LdapRoles|Namespace|Otherwise|Overwrite|Parameter|Read-Only|ReadMount|Redirects|Separator|SoftReset|Undefined|Variables|@Include|AutoWrap|BoldAttr|ClearTab|Constant|Contains|Continue|Critical|CursorUp|DHighTop|Encoding|EraseBOL|EraseBOS|EraseEOL|EraseEOS|For-Each|Function|Generate|Includes|KvSecret|LdapRole|MarkDown|Markdown|Metadata|Multiply|Negative|No-Flush|Password|Position|Positive|Redirect|ScrollUp|SetStyle|SetTitle|Subtract|Template|Terminal|Undelete|Aliases|Columns|Comment|Compact|Compile|Connect|Contain|DECSCNM|DbRoles|Declare|Default|Defined|Destroy|DimAttr|DrawBox|Else-If|End-For|Exclude|Exhibit|Greater|Headers|Include|Matches|Maximum|No-Echo|Options|Prepend|Product|Quoting|Records|Replace|Request|Results|Seconds|Secrets|Set-Key|Through|Timeout|Verbose|Version|Warning|Wrapper|Accept|Append|Assert|Assign|Blocks|Cached|Caches|Choose|Column|Config|Create|DbRole|Define|Delete|Digest|Divide|ElseIf|End-If|Equals|Extend|Filter|Follow|Giving|Global|Header|Indent|Insert|Method|Mounts|Object|Offset|Output|Printf|Record|Remove|Repeat|Result|Return|Rotate|Search|Second|Secret|Secure|Select|SetTab|Sorted|Source|Unique|Unless|Unlock|Update|Values|Verify|Abort|Array|Attrs|Basic|Batch|Begin|Block|Break|Bytes|Cache|Chain|Close|Const|Debug|Empty|Equal|Error|Field|Files|First|Flush|Index|Input|Jinja|Level|Limit|Lines|Local|Match|Mount|Nulls|Param|Patch|Paths|Print|Reset|Scope|Sleep|Strip|Style|Times|Token|Trace|Unset|Until|Using|Vault|Where|While|Write|Args|Auth|Auto|Base|Body|Call|Char|Data|Does|Down|Each|Echo|Else|Even|Exit|File|From|Head|Host|Http|Info|Into|Item|JSON|Junk|Keep|Keys|Last|Ldap|Left|Less|Line|List|Load|Lock|Meta|Next|Only|Open|Page|Pass|Post|Read|Root|Size|Sort|Step|Swap|Text|Than|Then|Thru|Time|Trim|Type|User|Warn|When|With|YAML|Add|All|And|Are|Asc|CAS|CSV|Des|End|For|Get|HCL|INI|Key|Log|Max|Nop|Not|OFS|ORS|Odd|Off|Per|Put|SSL|Set|URL|Ver|Zip|As|At|By|If|In|Is|No|Of|On|Or|To|Up)(?![.\w-])", Keyword),
            (r"(?i)\b(:?Backslash|Newline|Escape|Period|Colon|Comma|False|Quote|Space|None|Null|True|Zero|Inf|Nan|Tab|∅|∞)\b", Name.Constant),
            (r"(?i)\b(?:CountTrailingZeroBits|CountLeadingZeroBits|GetCurrentDirectory|LdapAttrGreaterThan|EscapeGlobPattern|ExtractAllMatches|LdapAttrNotExists|ExtractKVMetadata|IsNotGreaterThan|LdapAttrLessThan|LdapAttrNotEqual|ListRemoveFirst|MdStrikeThrough|MdUnorderedList|LdapAttrBetween|LdapAttrMatches|CompilePattern|IsAlphaNumeric|ListRemoveLast|FormatDuration|FormatDateTime|LdapAttrEquals|LdapAttrExists|IsGreaterThan|IsNotLessThan|CountZeroBits|HighestOneBit|DirectoryName|GlobToPattern|EscapePattern|RoundMultiple|FloorMultiple|GetWeekOfYear|MdOrderedList|GetCacheUsage|LdapFilterAnd|LdapFilterNot|ExtractKVData|IsNotEqualTo|DoesNotMatch|IsDictionary|Base64Encode|Base64Decode|CountOneBits|LowestOneBit|ReverseBytes|PatternFlags|ExtractMatch|RegexReplace|RemovePrefix|RemoveSuffix|CombineUsing|CombineLists|CeilMultiple|GetUtcOffset|GetMonthName|GetDayOfWeek|GetDayOfYear|MdBlockQuote|RightJustify|RandomChoice|RandomSample|TranslateStr|LdapFilterOr|ToLdapFilter|DurationToMs|MsToDuration|GetKeyValue|SetKeyValue|ParseBinary|RotateRight|ReverseBits|ExtractBits|IsDirectory|GetFileInfo|IsPrintable|IsTitleCase|ContainsAll|ListPrepend|ListReplace|GetDateTime|GetTimeZone|MdCodeBlock|LeftJustify|IsLessThan|IsNegative|IsPositive|IsNotEmpty|MatchesAll|Dictionary|LookupItem|ParseOctal|RotateLeft|ExpandPath|PathExists|RemoveFile|ReverseStr|Capitalize|RightStrip|StartsWith|ExpandTabs|ShortenStr|PrependStr|ReplaceStr|StripNulls|FormatJSON|ListAppend|ListRemove|ListInsert|ShiftRight|GetDayName|MdEmphasis|SplitLines|IsFunction|EmptyCache|LdapAttrGE|LdapAttrLE|LdapEscape|IsEqualTo|IsBetween|IsNotNone|ToBoolean|IsBoolean|ToInteger|IsInteger|DefaultTo|GetValues|RemoveKey|HexEncode|HexDecode|ToggleBit|ListFiles|IsPattern|StringLen|TitleCase|IsDecimal|IsNumeric|LeftStrip|AppendStr|Enumerate|FirstItem|ParseJSON|ParseYAML|ShiftLeft|GetMinute|GetSecond|MdHeading|MultiMode|PVariance|EncodeUrl|ToNumber|IsNumber|IsFinite|ToString|IsString|ToBinary|ParseInt|ParseHex|ClearBit|IsBitSet|FloorDiv|BaseName|CaseFold|SwapCase|EndsWith|RightStr|RIndexOf|RFindStr|LastItem|Contains|ParseCSV|ParseHCL|ParseINI|GetMonth|MdStrong|MdEscape|Checksum|ZeroFill|Variance|ParseUrl|ToFloat|IsFloat|IsEmpty|Matches|GetKeys|ToOctal|SetBits|IsAlpha|IsAscii|IsDigit|IsLower|IsSpace|IsUpper|LeftStr|CountOf|IndexOf|FindStr|Reverse|IsNotIn|IsFalse|GetHour|GetYear|MdImage|IsNone|IsZero|BitAnd|BitXor|BitNot|SetBit|DivMod|IsFile|SubStr|Negate|Length|Unique|IsList|ToList|IsTrue|IsEven|Plural|Format|GetDay|MdCode|MdLink|Center|Random|RSplit|Median|PStdev|Clamp|IsInf|IsNan|ToHex|BitOr|Lower|Upper|Strip|Clone|Apply|Trunc|Floor|Round|IsOdd|Slice|Split|Stdev|Type|Sign|Hash|Repr|Sort|Item|IsIn|Join|List|Ceil|Pred|Succ|Head|Tail|Mean|Mode|Add|Sum|Div|Not|Abs|Mod|Mul|Pow|Sub|Chr|Ord|Max|Min|Id)(?=\s*\()", Name.Function),

        ]
    }
