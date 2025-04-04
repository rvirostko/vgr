#! /bin/bash

../vgr.py <<EOF || echo "FAILED"

Set a To "hello  "
Set b to "  Hello"
# Build up a dictionary
Set d.a To a
Set d.b To b
Set d.c To 5
Set d.d To 5.1
Set d.e To True
# We use the same values in the dictionary for our array
Set c To [d.a, d.b, d.c, d.d, d.e]

Set fmt = "{}:\n" + ("    {!r} \u21D2 {!r}\n" * 4) + "\n"

Print "=" * 78

Printf fmt, "Capitalize()", a, a.Capitalize(), b, b.Capitalize(), c, c.Capitalize(), d, d.Capitalize()
Printf fmt, "CaseFold()", a, a.CaseFold(), b, b.CaseFold(), c, c.CaseFold(), d, d.CaseFold()
Printf fmt, "Lower()", a, a.Lower(), b, b.Lower(), c, c.Lower(), d, d.Lower()
Printf fmt, "SwapCase()", a, a.SwapCase(), b, b.SwapCase(), c, c.SwapCase(), d, d.SwapCase()
Printf fmt, "TitleCase()", a, a.TitleCase(), b, b.TitleCase(), c, c.TitleCase(), d, d.TitleCase()
Printf fmt, "Upper()", a, a.Upper(), b, b.Upper(), c, c.Upper(), d, d.Upper()
Printf fmt, "IsAlnum()", a, a.IsAlnum(), b, b.IsAlnum(), c, c.IsAlnum(), d, d.IsAlnum()
Printf fmt, "IsAlpha()", a, a.IsAlpha(), b, b.IsAlpha(), c, c.IsAlpha(), d, d.IsAlpha()
Printf fmt, "IsAscii()", a, a.IsAscii(), b, b.IsAscii(), c, c.IsAscii(), d, d.IsAscii()
Printf fmt, "IsDecimal()", a, a.IsDecimal(), b, b.IsDecimal(), c, c.IsDecimal(), d, d.IsDecimal()
Printf fmt, "IsDigit()", a, a.IsDigit(), b, b.IsDigit(), c, c.IsDigit(), d, d.IsDigit()
Printf fmt, "IsIdentifier()", a, a.IsIdentifier(), b, b.IsIdentifier(), c, c.IsIdentifier(), d, d.IsIdentifier()
Printf fmt, "IsLower()", a, a.IsLower(), b, b.IsLower(), c, c.IsLower(), d, d.IsLower()
Printf fmt, "IsNumeric()", a, a.IsNumeric(), b, b.IsNumeric(), c, c.IsNumeric(), d, d.IsNumeric()
Printf fmt, "IsPrintable()", a, a.IsPrintable(), b, b.IsPrintable(), c, c.IsPrintable(), d, d.IsPrintable()
Printf fmt, "IsSpace()", a, a.IsSpace(), b, b.IsSpace(), c, c.IsSpace(), d, d.IsSpace()
Printf fmt, "IsTitle()", a, a.IsTitle(), b, b.IsTitle(), c, c.IsTitle(), d, d.IsTitle()
Printf fmt, "IsUpper()", a, a.IsUpper(), b, b.IsUpper(), c, c.IsUpper(), d, d.IsUpper()

Printf fmt, "Strip()", a, a.Strip(), b, b.Strip(), c, c.Strip(), d, d.Strip()
Printf fmt, "Strip(\"o\")", a, a.Strip("o"), b, b.Strip("o"), c, c.Strip("o"), d, d.Strip("o")
Printf fmt, "LeftStrip()", a, a.LeftStrip(), b, b.LeftStrip(), c, c.LeftStrip(), d, d.LeftStrip()
Printf fmt, "LeftStrip(\"h\")", a, a.LeftStrip("h"), b, b.LeftStrip("h"), c, c.LeftStrip("h"), d, d.LeftStrip("h")
Printf fmt, "RightStrip()", a, a.RightStrip(), b, b.RightStrip(), c, c.RightStrip(), d, d.RightStrip()
Printf fmt, "RightStrip(\"o\")", a, a.RightStrip("o"), b, b.RightStrip("o"), c, c.RightStrip("o"), d, d.RightStrip("o")
Printf fmt, "RemovePrefix(\"h\")", a, a.RemovePrefix("h"), b, b.RemovePrefix("h"), c, c.RemovePrefix("h"), d, d.LeftStrip("h")
Printf fmt, "RemoveSuffix(\"o\")", a, a.RemoveSuffix("o"), b, b.RemoveSuffix("o"), c, c.RemoveSuffix("o"), d, d.RemoveSuffix("o")

Printf fmt, "StartsWith(\"h\")", a, a.StartsWith("h"), b, b.StartsWith("h"), c, c.StartsWith("h"), d, d.StartsWith("h")
Printf fmt, "EndsWith(\"o\")", a, a.EndsWith("o"), b, b.EndsWith("o"), c, c.EndsWith("o"), d, d.EndsWith("o")

Printf fmt, "ExpandTabs(2)", a, a.ExpandTabs(2), b, b.ExpandTabs(2), c, c.ExpandTabs(2), d, d.ExpandTabs(2)
Printf fmt, "LeftStr(1)", a, a.LeftStr(1), b, b.LeftStr(1), c, c.LeftStr(1), d, d.LeftStr(1)
Printf fmt, "RightStr(1)", a, a.RightStr(1), b, b.RightStr(1), c, c.RightStr(1), d, d.RightStr(1)
Printf fmt, "SubStr(1,2)", a, a.SubStr(1,2), b, b.SubStr(1,2), c, c.SubStr(1,2), d, d.SubStr(1,2)

Printf fmt, "CountOf(\"l\")", a, a.CountOf("l"), b, b.CountOf("l"), c, c.CountOf("l"), d, d.CountOf("l")
Printf fmt, "IndexOf(\"l\")", a, a.IndexOf("l"), b, b.IndexOf("l"), c, c.IndexOf("l"), d, d.IndexOf("l")
Printf fmt, "IndexOf(\"z\")", a, a.IndexOf("z"), b, b.IndexOf("z"), c, c.IndexOf("z"), d, d.IndexOf("z")
Printf fmt, "RIndexOf(\"l\")", a, a.RIndexOf("l"), b, b.RIndexOf("l"), c, c.RIndexOf("l"), d, d.RIndexOf("l")
Printf fmt, "RIndexOf(\"z\")", a, a.RIndexOf("z"), b, b.RIndexOf("z"), c, c.RIndexOf("z"), d, d.RIndexOf("z")

Set s2 = ["1", "2", "3"]
Set s3 = [1, 2, 3]
Set s4 = [1, [2]]
Set s5 = [3, True, None]

Set label = "Append(\"1\", \"2\", \"3\")"
Printf fmt, label, a, a.Append("1", "2", "3"), b, b.Append("1", "2", "3"), c, c.Append("1", "2", "3"), d, d.Append("1", "2", "3")
Set label = "Append(" + s2.Repr() + ")"
Printf fmt, label, a, a.Append(s2), b, b.Append(s2), c, c.Append(s2), d, d.Append(s2)
Set label = "Append(" + s3.Repr() + ")"
Printf fmt, label, a, a.Append(s3), b, b.Append(s3), c, c.Append(s3), d, d.Append(s3)
Set label = "Append(" + s4.Repr() + ", 3)"
Printf fmt, label, a, a.Append(s4, 3), b, b.Append(s4, 3), b, b.Append(s4, 3), b, b.Append(s4, 3)
Set label = "Append(" + s4.Repr() + ", " + s5.Repr() + ")"
Printf fmt, label, a, a.Append(s4, s5), b, b.Append(s4, s5), c, c.Append(s4, s5), d, d.Append(s4, s5)

Set label = "Prepend(\"1\", \"2\", \"3\")"
Printf fmt, label, a, a.Prepend("1", "2", "3"), b, b.Prepend("1", "2", "3"), c, c.Prepend("1", "2", "3"), d, d.Prepend("1", "2", "3")
Set label = "Prepend(" + s2.Repr() + ")"
Printf fmt, label, a, a.Prepend(s2), b, b.Prepend(s2), c, c.Prepend(s2), d, d.Prepend(s2)
Set label = "Prepend(" + s3.Repr() + ")"
Printf fmt, label, a, a.Prepend(s3), b, b.Prepend(s3), c, c.Prepend(s3), d, d.Prepend(s3)
Set label = "Prepend(" + s4.Repr() + ", 3)"
Printf fmt, label, a, a.Prepend(s4, 3), b, b.Prepend(s4, 3), b, b.Prepend(s4, 3), b, b.Prepend(s4, 3)
Set label = "Prepend(" + s4.Repr() + ", " + s5.Repr() + ")"
Printf fmt, label, a, a.Prepend(s4, s5), b, b.Prepend(s4, s5), c, c.Prepend(s4, s5), d, d.Prepend(s4, s5)

# Split()
# RSplit()
# Replace()
# RegExReplace()
# CompilePattern()
# Translate


EOF
