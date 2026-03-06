#!/usr/bin/env node
/**
 * convert_md_to_pdf.js — Convert markdown files to PDF
 *
 * Usage:
 *   node scripts/convert_md_to_pdf.js <path> [--recursive]
 *
 *   <path> can be:
 *     - A single .md file  → converts just that file
 *     - A directory        → converts all .md files in that directory
 *
 *   --recursive   Also convert .md files in subdirectories (only applies to directory input)
 *
 * Each .pdf is written alongside its .md source (same directory, same base name).
 * Original .md files are never modified.
 * Exits with code 1 if any conversion fails.
 */

const { mdToPdf } = require('md-to-pdf');
const path = require('path');
const fs = require('fs');

const CSS = `
  body {
    font-size: 14px;
    max-width: none;
    padding: 20px 32px;
    line-height: 1.6;
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
    background: #f7f7f7;
  }
  th {
    background: #e8e8e8;
    font-weight: 600;
  }
  blockquote {
    border-left: 4px solid #4a90d9;
    background: #f0f6ff;
    margin: 1em 0;
    padding: 0.6em 1em;
    color: #333;
  }
  blockquote p {
    margin: 0;
  }
  code {
    background: #f4f4f4;
    padding: 1px 4px;
    border-radius: 3px;
    font-size: 0.9em;
  }
  pre {
    background: #f4f4f4;
    padding: 12px;
    border-radius: 4px;
    overflow-x: auto;
  }
  h1, h2, h3 {
    margin-top: 1.4em;
  }
`;

async function convertFile(mdPath) {
  const absPath = path.resolve(mdPath);
  const pdfPath = absPath.replace(/\.md$/, '.pdf');

  try {
    await mdToPdf(
      { path: absPath },
      {
        dest: pdfPath,
        css: CSS,
        pdf_options: {
          format: 'A4',
          margin: { top: '20mm', bottom: '20mm', left: '18mm', right: '18mm' },
          printBackground: true,
        },
      }
    );
    console.log(`  ✓ ${path.basename(pdfPath)}`);
    return true;
  } catch (err) {
    console.error(`  ✗ ${path.basename(mdPath)} — ${err.message}`);
    return false;
  }
}

function collectMdFiles(targetPath, recursive) {
  const stat = fs.statSync(targetPath);

  if (stat.isFile()) {
    if (!targetPath.endsWith('.md')) {
      console.error(`Error: "${targetPath}" is not a .md file.`);
      process.exit(1);
    }
    return [targetPath];
  }

  if (stat.isDirectory()) {
    const files = [];
    const entries = fs.readdirSync(targetPath, { withFileTypes: true });
    for (const entry of entries) {
      const entryPath = path.join(targetPath, entry.name);
      if (entry.isFile() && entry.name.endsWith('.md')) {
        files.push(entryPath);
      } else if (recursive && entry.isDirectory()) {
        files.push(...collectMdFiles(entryPath, recursive));
      }
    }
    return files;
  }

  console.error(`Error: "${targetPath}" is not a file or directory.`);
  process.exit(1);
}

async function main() {
  const args = process.argv.slice(2);
  const recursive = args.includes('--recursive');
  const positional = args.filter(a => !a.startsWith('--'));

  if (positional.length === 0) {
    console.error('Usage: node scripts/convert_md_to_pdf.js <path> [--recursive]');
    process.exit(1);
  }

  const targetPath = positional[0];

  if (!fs.existsSync(targetPath)) {
    console.error(`Error: Path not found: "${targetPath}"`);
    process.exit(1);
  }

  const files = collectMdFiles(targetPath, recursive);

  if (files.length === 0) {
    console.log('No .md files found.');
    process.exit(0);
  }

  console.log(`Converting ${files.length} file(s)...`);

  const results = [];
  for (const f of files) {
    results.push(await convertFile(f));
  }

  const failed = results.filter(r => !r).length;
  const passed = results.length - failed;
  console.log(`\nDone: ${passed} succeeded, ${failed} failed.`);

  if (failed > 0) process.exit(1);
}

main();
