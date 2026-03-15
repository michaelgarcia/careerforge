#!/usr/bin/env python3
"""Convert .docx to .pdf using docx2pdf (Word COM on Windows with Word installed)."""
import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to .docx file")
    args = parser.parse_args()

    docx_path = Path(args.input).resolve()
    if not docx_path.exists():
        print(f"Error: {docx_path} does not exist", file=sys.stderr)
        sys.exit(1)

    pdf_path = docx_path.with_suffix(".pdf")

    try:
        from docx2pdf import convert
        convert(str(docx_path), str(pdf_path))
    except Exception as e:
        print(f"Error converting to PDF: {e}", file=sys.stderr)
        sys.exit(1)

    size_kb = pdf_path.stat().st_size / 1024
    print(f"Generated: {pdf_path} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
