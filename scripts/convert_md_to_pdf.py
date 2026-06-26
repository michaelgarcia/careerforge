#!/usr/bin/env python3
"""
convert_md_to_pdf.py — Convert Markdown files to PDF.

Usage:
  python scripts/convert_md_to_pdf.py <path> [--recursive]

  <path> can be:
    - A single .md file  → converts just that file
    - A directory        → converts all .md files in that directory

  --recursive   Also convert .md files in subdirectories (only with directory input)

Each .pdf is written alongside its .md source (same directory, same base name).
Original .md files are never modified.
Exits with code 1 if any conversion fails.

Requires: pip install markdown xhtml2pdf
"""

import argparse
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

try:
    import markdown
    from xhtml2pdf import pisa
except ImportError as e:
    print(f'Error: Missing dependency — {e}', file=sys.stderr)
    print('Install with: pip install markdown xhtml2pdf', file=sys.stderr)
    sys.exit(1)


CSS_STYLES = """
@page {
    size: A4;
    margin: 20mm 18mm;
}
body {
    font-family: Helvetica, Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #333;
}
table {
    border-collapse: collapse;
    width: 100%;
    margin: 1em 0;
}
th, td {
    border: 1px solid #ccc;
    padding: 6px 10px;
    text-align: left;
}
tr:nth-child(even) td {
    background-color: #f7f7f7;
}
th {
    background-color: #e8e8e8;
    font-weight: bold;
}
blockquote {
    border-left: 4px solid #4a90d9;
    background-color: #f0f6ff;
    margin: 1em 0;
    padding: 0.6em 1em;
    color: #333;
}
blockquote p {
    margin: 0;
}
code {
    background-color: #f4f4f4;
    padding: 1px 4px;
    border-radius: 3px;
    font-size: 0.9em;
    font-family: "Courier New", Courier, monospace;
}
pre {
    background-color: #f4f4f4;
    padding: 12px;
    border-radius: 4px;
}
pre code {
    padding: 0;
    background-color: transparent;
}
h1, h2, h3 {
    margin-top: 1.4em;
}
"""

MD_EXTENSIONS = ['tables', 'fenced_code', 'nl2br', 'sane_lists']


def convert_file(md_path: Path) -> bool:
    pdf_path = md_path.with_suffix('.pdf')
    try:
        md_text = md_path.read_text(encoding='utf-8')
        html_body = markdown.markdown(md_text, extensions=MD_EXTENSIONS)
        html = (
            '<html><head><meta charset="utf-8">'
            f'<style>{CSS_STYLES}</style>'
            f'</head><body>{html_body}</body></html>'
        )
        with open(pdf_path, 'wb') as pdf_file:
            result = pisa.CreatePDF(
                src=html,
                dest=pdf_file,
                encoding='utf-8',
                path=str(md_path.parent),
            )
        if result.err:
            raise RuntimeError(f'{result.err} rendering error(s)')
        print(f'  ✓ {pdf_path.name}')
        return True
    except Exception as e:
        print(f'  ✗ {md_path.name} — {e}', file=sys.stderr)
        return False


def collect_md_files(target: Path, recursive: bool) -> list:
    if target.is_file():
        if target.suffix != '.md':
            print(f'Error: "{target}" is not a .md file.', file=sys.stderr)
            sys.exit(1)
        return [target]
    if target.is_dir():
        pattern = '**/*.md' if recursive else '*.md'
        return sorted(target.glob(pattern))
    print(f'Error: "{target}" is not a file or directory.', file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='Convert Markdown files to PDF')
    parser.add_argument('path', help='Path to a .md file or directory')
    parser.add_argument('--recursive', action='store_true',
                        help='Also convert .md files in subdirectories')
    args = parser.parse_args()

    target = Path(args.path)
    if not target.exists():
        print(f'Error: Path not found: "{target}"', file=sys.stderr)
        sys.exit(1)

    files = collect_md_files(target, args.recursive)
    if not files:
        print('No .md files found.')
        sys.exit(0)

    print(f'Converting {len(files)} file(s)...')
    results = [convert_file(f) for f in files]
    failed = results.count(False)
    print(f'\nDone: {len(results) - failed} succeeded, {failed} failed.')
    if failed:
        sys.exit(1)


if __name__ == '__main__':
    main()
