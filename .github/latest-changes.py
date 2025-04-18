from pathlib import Path


root = Path(__file__).parent.parent
with open(root / 'CHANGES.md', 'rt') as changes, open(root / 'LATEST-CHANGES.md', 'wt') as latest_changes:
    line = None
    # read past content until we reach a line starting with "- "
    while not (line := next(changes)).startswith('- '):
        pass

    # write the first matching line, and all consecutive matching lines
    latest_changes.write(line)
    while (line := next(changes)).startswith('- '):
        latest_changes.write(line)
