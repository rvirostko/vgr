from pathlib import Path
from importlib.metadata import (
    distribution,
    metadata,
)
import re

# pylint: disable=bare-except
def read_license_file():
    """Read license text in both dev and installed environments."""
    try:
        # When installed: read from package metadata
        dist = distribution('vgr')
        license_files = dist.files
        for file in license_files:
            if file.match('*/LICENSE.md') or file.name == 'LICENSE.md':
                return file.read_text()
    except:
        pass
    # Fallback for development: navigate up from package location
    try:
        package_dir = Path(__file__).parent  # vgr/__init__.py location
        license_path = package_dir.parent.parent / 'LICENSE.md'  # up to project root
        if license_path.exists():
            return license_path.read_text()
    except:
        pass
    return "**License file not found**"

# pylint: disable=bare-except
def get_authors():
    """Get authors from package metadata as Markdown."""
    try:
        meta = metadata('vgr')
        author_email = meta.get('Author-Email', '')
        if not author_email: return "Authors not available"
        pattern = r'([^<,]+?)\s*<([^>]+)>'
        matches = re.findall(pattern, author_email)
        if not matches: return author_email  # Return raw if parsing fails
        # Format as Markdown list
        lines = [f"- **{name.strip()}** — {email.strip()}"
                 for name, email in matches]
        return '\n'.join(lines)
    except:  # pylint: disable=bare-except
        return "Package metadata error"
