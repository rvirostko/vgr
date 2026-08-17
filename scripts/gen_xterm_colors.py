#! env python3
import json
import urllib.request
import sys

COLOR_NAMES = [
    "Black",
    "Red",
    "Green",
    "Yellow",
    "Blue",
    "Magenta",
    "Cyan",
    "White",
    "Grey",
    "BrightRed",
    "BrightGreen",
    "BrightYellow",
    "BrightBlue",
    "BrightMagenta",
    "BrightCyan",
    "BrightWhite"
]

def main():
    url = "https://jonasjacek.github.io/colors/data.json"
    with urllib.request.urlopen(url) as resp:
        data = json.load(resp)
    colors, aux = build_color_array(data)
    print(f"\"\"\"\nGenerated from {url}\n\"\"\"")
    print()
    print("# The index of the named color is its value")
    print("TERM_COLORS = [")
    for color in colors:
        print(f"    {color!r},")
    print("]")
    print()
    print("# Consult after checking TERM_COLORS first")
    print("AUX_COLORS = {")
    for key, value in aux.items():
        if key not in colors:
            print(f"    {key!r}: {value!r},")
    print("}")
    print()

def build_color_array(data):
    color_array = [None] * 256
    aux_names = {}
    name_to_index = {}
    # Prepopulate with COLOR_NAMES
    for i, name in enumerate(COLOR_NAMES):
        color_array[i] = name
        name_to_index[name.casefold()] = i

    for item in data:
        name = item["name"].replace('Gray', 'Grey')
        idx = item["colorId"]
        if not (0 <= idx < 256):
            print(f"Index error {idx} for {name!r}", file=sys.stderr)
            continue
        # Check if the slot at the index is already occupied
        if color_array[idx] is not None:
            if color_array[idx].casefold() != name.casefold():
                print(
                    f"Conflict at {idx} {name!r}: {color_array[idx]!r} is already present",
                    file=sys.stderr
                )
                aux_names[name] = idx
            continue
        # Check if the name is already used elsewhere
        name_lower = name.casefold()
        if name_lower in name_to_index:
            prev_idx = name_to_index[name_lower]
            print(
                f"Name conflict at {idx} for {name!r}: already used at index {prev_idx}",
                file=sys.stderr
            )
            continue
        color_array[idx] = name
        name_to_index[name_lower] = idx
    # Fill in any remaining None slots
    for i in range(256):
        if color_array[i] is None:
            color_array[i] = f"Color{i}"
    return (color_array, aux_names)

if __name__ == "__main__":
    main()
