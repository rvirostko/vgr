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
            (r"(?i)(?<![.\w_])(:?RotateDbConnectionCredentials|GenerateDbRoleCredentials|RotateDbRoleCredentials|CreateDbConnection|UpdateDbConnection|DeleteDbConnection|CreateLdapLibrary|UpdateLdapLibrary|DeleteLdapLibrary|ListLdapLibraries|ListDbConnections|ResetDbConnection|MoveCursorToLine|DefaultNamespace|DeleteKvMetadata|UndeleteKvSecret|ReadDbConnection|MoveCursorToCol|GetTerminalSize|CreateNamespace|UpdateNamespace|DeleteNamespace|UnlockNamespace|DestroyKvSecret|ReadLdapLibrary|Authentication|StrikeThruAttr|ListNamespaces|CreateKvSecret|ReadKvMetadata|UpdateKvSecret|DeleteKvSecret|CreateLdapRole|UpdateLdapRole|DeleteLdapRole|RotateLdapRole|Call-Function|Corresponding|RestoreCursor|CursorVisible|CursorForward|AlignmentTest|SetForeground|SetBackground|UnderlineAttr|ReadNamespace|LockNamespace|ListKvSecrets|PatchKvSecret|ListLdapRoles|End-Function|Accept-Input|HTTP-Version|MoveCursorTo|GetCursorPos|EraseDisplay|ScrollRegion|SmoothScroll|SetClipboard|ClearAllTabs|ReadKvSecret|ReadLdapRole|CreateDbRole|UpdateDbRole|DeleteDbRole|Dereference|Operational|ClearScreen|RaiseWindow|SetIconName|ItalicsAttr|ReverseAttr|DHighBottom|CreateMount|UpdateMount|DeleteMount|ListDbRoles|Description|End-Repeat|End-Unless|End-Choose|Dictionary|Remove-Key|Create-Zip|Descending|Terminator|Disconnect|Parameters|Connection|Attributes|HomeCursor|SaveCursor|ShowCursor|HideCursor|CursorDown|CursorBack|InsertLine|DeleteLine|InsertChar|DeleteChar|ScrollDown|OriginMode|InsertMode|PrintDHigh|RepeatChar|ResetAttrs|HiddenAttr|DoubleWide|SingleWide|ListMounts|ReadDbRole|End-Until|End-While|Undefined|Otherwise|Constants|Separator|Overwrite|Ascending|Cartesian|Delimiter|Character|Variables|Redirects|Parameter|Read-Only|EraseChar|EraseLine|SoftReset|HardReset|DeIconify|BlinkAttr|DrawHLine|DrawVLine|ReadMount|BlockSize|Namespace|Terminal|Encoding|Function|Constant|For-Each|Continue|Contains|Positive|Negative|Subtract|Multiply|Includes|Markdown|No-Flush|Position|MarkDown|Template|Redirect|Password|CursorUp|EraseEOL|EraseBOL|EraseEOS|EraseBOS|ScrollUp|AutoWrap|ClearTab|SetTitle|SetStyle|BoldAttr|DHighTop|Metadata|Headers|Seconds|Declare|Compile|End-For|Greater|Matches|Contain|Defined|Through|Verbose|No-Echo|Set-Key|Exhibit|Warning|Comment|Include|Exclude|Prepend|Replace|Records|Columns|Product|Compact|Wrapper|Quoting|Default|Request|Connect|Options|Maximum|Timeout|Aliases|DECSCNM|DimAttr|DrawBox|Results|Secrets|Version|Header|Values|Second|Giving|Output|Global|Define|Cached|End-If|Repeat|Unless|Return|Equals|Choose|Accept|Secure|Assign|Divide|Remove|Source|Object|Assert|Printf|Record|Append|Extend|Create|Unique|Insert|Column|Select|Offset|Sorted|Indent|Blocks|Method|Delete|Verify|Digest|Follow|Search|Filter|SetTab|Update|Result|Secret|Config|Files|Nulls|Error|Input|Begin|Using|Local|Const|Cache|Times|Until|While|Break|Equal|Match|Empty|Debug|Sleep|Unset|Reset|Lines|Abort|Print|Field|Flush|Level|Close|Paths|Index|First|Where|Limit|Array|Style|Jinja|Batch|Strip|Chain|Patch|Trace|Basic|Param|Write|Attrs|Scope|Vault|Token|Block|Bytes|File|Call|Each|Step|Next|Then|Else|Time|Less|Than|Does|Even|When|Thru|Echo|Pass|From|Down|With|Swap|Args|Data|Load|Type|Text|JSON|Line|YAML|Warn|Info|Open|Read|Junk|Exit|Sort|List|Into|Item|Last|Keys|Root|Char|Auto|Trim|Left|Keep|Http|Head|Post|Auth|User|Body|Ldap|Only|Page|Size|Base|Host|Meta|End|For|Not|All|Odd|Off|Nop|Set|Add|Key|And|CSV|HCL|INI|Per|OFS|ORS|Log|Zip|Asc|Des|URL|Get|Put|SSL|Max|Are|Ver|CAS|To|Is|As|In|If|On|No|Up|By|At|Of|Or)(?![.\w-])", Keyword),
            (r"(?i)\b(:?Backslash|Newline|Escape|Period|Colon|Comma|False|Quote|Space|None|Null|True|Zero|Inf|Nan|Tab|∅|∞)\b", Name.Constant),
            (r"(?i)\b(?:CountTrailingZeroBits|CountLeadingZeroBits|GetCurrentDirectory|LdapAttrGreaterThan|ExtractAllMatches|LdapAttrNotExists|ExtractKVMetadata|IsNotGreaterThan|LdapAttrLessThan|LdapAttrNotEqual|ListRemoveFirst|MdStrikeThrough|MdUnorderedList|LdapAttrBetween|LdapAttrMatches|CompilePattern|FormatDuration|FormatDateTime|IsAlphaNumeric|ListRemoveLast|LdapAttrEquals|LdapAttrExists|CountZeroBits|DirectoryName|FloorMultiple|GetWeekOfYear|HighestOneBit|IsGreaterThan|IsNotLessThan|MdOrderedList|RoundMultiple|LdapFilterAnd|LdapFilterNot|ExtractKVData|Base64Decode|Base64Encode|CeilMultiple|CombineLists|CombineUsing|CountOneBits|DoesNotMatch|ExtractMatch|GetDayOfWeek|GetDayOfYear|GetMonthName|GetUtcOffset|IsDictionary|IsNotEqualTo|LowestOneBit|MdBlockQuote|RandomChoice|RegexReplace|RemovePrefix|RemoveSuffix|ReverseBytes|RightJustify|TranslateStr|LdapFilterOr|ToLdapFilter|DurationToMs|MsToDuration|ContainsAll|ExtractBits|GetDateTime|GetKeyValue|GetTimeZone|IsDirectory|IsPrintable|LeftJustify|ListPrepend|ListReplace|MdCodeBlock|ParseBinary|ReverseBits|RotateRight|SetKeyValue|Capitalize|Dictionary|ExpandTabs|PathExists|FormatJSON|GetDayName|IsFunction|IsLessThan|IsNegative|IsNotEmpty|IsPositive|ListAppend|ListInsert|ListRemove|LookupItem|MatchesAll|MdEmphasis|ParseOctal|PrependStr|RemoveFile|ReplaceStr|ReverseStr|ShiftRight|RightStrip|RotateLeft|ShortenStr|SplitLines|StartsWith|StripNulls|LdapAttrGE|LdapAttrLE|LdapEscape|AppendStr|DefaultTo|EncodeUrl|Enumerate|FirstItem|GetMinute|GetSecond|GetValues|HexDecode|HexEncode|IsBetween|IsBoolean|IsDecimal|IsEqualTo|IsInteger|IsNotNone|IsNumeric|IsPattern|ShiftLeft|LeftStrip|MdHeading|MultiMode|ParseJSON|ParseYAML|PVariance|RemoveKey|StringLen|TitleCase|ToBoolean|ToggleBit|ToInteger|BaseName|CaseFold|Checksum|ClearBit|Contains|EndsWith|FloorDiv|GetMonth|IsBitSet|IsFinite|IsNumber|IsString|LastItem|MdStrong|ParseCSV|ParseHCL|ParseHex|ParseINI|ParseInt|ParseUrl|RFindStr|RightStr|RIndexOf|SwapCase|ToBinary|ToNumber|ToString|Variance|ZeroFill|CountOf|FindStr|GetHour|GetKeys|GetYear|IndexOf|IsAlpha|IsAscii|IsDigit|IsEmpty|IsFalse|IsFloat|IsLower|IsNotIn|IsSpace|IsTitleCase|IsUpper|LeftStr|Matches|Reverse|SetBits|ToFloat|ToOctal|BitAnd|BitNot|BitXor|Center|DivMod|Format|GetDay|IsEven|IsFile|IsList|IsNone|IsTrue|IsZero|Length|MdCode|MdLink|Median|Negate|Plural|PStdev|Random|RSplit|SetBit|SubStr|ToList|Unique|Apply|Ascii|BitOr|Clamp|Clone|Floor|IsInf|IsNan|IsOdd|Lower|Round|Slice|Split|Stdev|Strip|ToHex|Trunc|Upper|Ceil|Hash|IsIn|Item|Join|List|Mean|Mode|Pred|Repr|Sign|Sort|Succ|Type|Abs|Add|Chr|Div|Max|Min|Mod|Mul|Not|Ord|Pow|Sub|Sum|Id)(?=\s*\()", Name.Function)
        ]
    }
