#!/usr/bin/env node

/**
 * generate_docx.js — Helper script for generating professional .docx documents.
 * 
 * Usage:
 *   node scripts/generate_docx.js --input content.json --output output.docx --type resume
 *   node scripts/generate_docx.js --input content.json --output output.docx --type cover_letter
 * 
 * The input JSON should contain structured content matching the expected schema.
 * This script is called by the resume-writer and cover-letter agents.
 * 
 * Requires: npm install -g docx
 * 
 * NOTE: This is a starter template. The agents may also generate .docx files
 * directly via inline Node.js scripts for more customization per-document.
 */

const fs = require('fs');
const path = require('path');

// Parse arguments
const args = process.argv.slice(2);
const getArg = (name) => {
  const idx = args.indexOf(`--${name}`);
  return idx !== -1 ? args[idx + 1] : null;
};

const inputPath = getArg('input');
const outputPath = getArg('output');
const docType = getArg('type') || 'resume';

if (!inputPath || !outputPath) {
  console.error('Usage: node generate_docx.js --input <content.json> --output <output.docx> [--type resume|cover_letter]');
  process.exit(1);
}

// Dynamic import of docx (supports both global and local installs)
let docx;
try {
  docx = require('docx');
} catch (e) {
  console.error('Error: "docx" package not found. Install it with: npm install -g docx');
  console.error('Or locally: npm install docx');
  process.exit(1);
}

const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle,
  WidthType, ShadingType, LevelFormat, PageBreak
} = docx;

// Read input content
const content = JSON.parse(fs.readFileSync(inputPath, 'utf8'));

/**
 * Generate a resume document from structured content.
 * 
 * Expected content schema:
 * {
 *   "personal": { "name", "title", "email", "phone", "linkedin", "location" },
 *   "summary": "Professional summary text",
 *   "skills": { "category_name": ["skill1", "skill2"] },
 *   "experience": [{ "company", "title", "dates", "location", "bullets": ["..."] }],
 *   "education": [{ "institution", "degree", "field", "date", "honors" }],
 *   "certifications": [{ "name", "issuer", "date" }],
 *   "style": { "font", "accent_color", "body_size_pt", ... }
 * }
 */
function generateResume(content) {
  const style = content.style || {};
  const font = style.font || 'Calibri';
  const bodySize = (style.body_size_pt || 11) * 2; // docx uses half-points
  const headingSize = (style.heading_size_pt || 13) * 2;
  const nameSize = (style.name_size_pt || 18) * 2;
  const accentColor = style.accent_color || '2B579A';
  const p = content.personal || {};

  const children = [];

  // Header — Name
  children.push(new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 40 },
    children: [new TextRun({ text: p.name || 'Candidate Name', font, size: nameSize, bold: true })]
  }));

  // Header — Title
  if (p.title) {
    children.push(new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 40 },
      children: [new TextRun({ text: p.title, font, size: bodySize + 2, color: accentColor })]
    }));
  }

  // Header — Contact line
  const contactParts = [p.email, p.phone, p.location, p.linkedin].filter(Boolean);
  if (contactParts.length > 0) {
    children.push(new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 200 },
      children: [new TextRun({ text: contactParts.join('  |  '), font, size: bodySize - 2 })]
    }));
  }

  // Helper: Section heading with divider
  const sectionHeading = (text) => new Paragraph({
    spacing: { before: 240, after: 80 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 1, color: accentColor, space: 4 } },
    children: [new TextRun({ text: text.toUpperCase(), font, size: headingSize, bold: true, color: accentColor })]
  });

  // Professional Summary
  if (content.summary) {
    children.push(sectionHeading('Professional Summary'));
    children.push(new Paragraph({
      spacing: { after: 120 },
      children: [new TextRun({ text: content.summary, font, size: bodySize })]
    }));
  }

  // Skills
  if (content.skills && Object.keys(content.skills).length > 0) {
    children.push(sectionHeading('Technical Skills'));
    for (const [category, skills] of Object.entries(content.skills)) {
      children.push(new Paragraph({
        spacing: { after: 60 },
        children: [
          new TextRun({ text: `${category}: `, font, size: bodySize, bold: true }),
          new TextRun({ text: skills.join(', '), font, size: bodySize })
        ]
      }));
    }
  }

  // Experience
  if (content.experience && content.experience.length > 0) {
    children.push(sectionHeading('Professional Experience'));
    for (const role of content.experience) {
      // Company and title line
      children.push(new Paragraph({
        spacing: { before: 160, after: 20 },
        children: [
          new TextRun({ text: role.title || '', font, size: bodySize, bold: true }),
          new TextRun({ text: `  —  ${role.company || ''}`, font, size: bodySize }),
        ]
      }));
      // Dates and location
      const meta = [role.dates, role.location].filter(Boolean).join('  |  ');
      if (meta) {
        children.push(new Paragraph({
          spacing: { after: 60 },
          children: [new TextRun({ text: meta, font, size: bodySize - 2, italics: true, color: '666666' })]
        }));
      }
      // Bullet points
      if (role.bullets) {
        for (const bullet of role.bullets) {
          children.push(new Paragraph({
            spacing: { after: 40 },
            indent: { left: 360, hanging: 180 },
            children: [new TextRun({ text: `•  ${bullet}`, font, size: bodySize })]
          }));
        }
      }
    }
  }

  // Education
  if (content.education && content.education.length > 0) {
    children.push(sectionHeading('Education'));
    for (const edu of content.education) {
      children.push(new Paragraph({
        spacing: { after: 60 },
        children: [
          new TextRun({ text: `${edu.degree || ''} in ${edu.field || ''}`, font, size: bodySize, bold: true }),
          new TextRun({ text: `  —  ${edu.institution || ''}`, font, size: bodySize }),
          new TextRun({ text: edu.date ? `  (${edu.date})` : '', font, size: bodySize - 2, color: '666666' }),
        ]
      }));
      if (edu.honors) {
        children.push(new Paragraph({
          spacing: { after: 40 },
          indent: { left: 360 },
          children: [new TextRun({ text: edu.honors, font, size: bodySize - 2, italics: true })]
        }));
      }
    }
  }

  // Certifications
  if (content.certifications && content.certifications.length > 0) {
    children.push(sectionHeading('Certifications'));
    for (const cert of content.certifications) {
      children.push(new Paragraph({
        spacing: { after: 40 },
        children: [
          new TextRun({ text: cert.name || '', font, size: bodySize, bold: true }),
          new TextRun({ text: `  —  ${cert.issuer || ''}`, font, size: bodySize }),
          new TextRun({ text: cert.date ? `  (${cert.date})` : '', font, size: bodySize - 2, color: '666666' }),
        ]
      }));
    }
  }

  return new Document({
    styles: {
      default: { document: { run: { font, size: bodySize } } }
    },
    sections: [{
      properties: {
        page: {
          size: { width: 12240, height: 15840 },
          margin: {
            top: Math.round((style.margin_top || 0.75) * 1440),
            bottom: Math.round((style.margin_bottom || 0.75) * 1440),
            left: Math.round((style.margin_left || 0.85) * 1440),
            right: Math.round((style.margin_right || 0.85) * 1440),
          }
        }
      },
      children
    }]
  });
}

/**
 * Generate a cover letter document.
 * 
 * Expected content schema:
 * {
 *   "personal": { "name", "email", "phone", "location" },
 *   "date": "February 13, 2026",
 *   "recipient": { "name", "title", "company", "address" },
 *   "salutation": "Dear Hiring Team,",
 *   "paragraphs": ["Opening...", "Body 1...", "Body 2...", "Closing..."],
 *   "closing": "Sincerely,",
 *   "style": { ... }
 * }
 */
function generateCoverLetter(content) {
  const style = content.style || {};
  const font = style.font || 'Calibri';
  const bodySize = (style.body_size_pt || 11) * 2;
  const p = content.personal || {};
  const r = content.recipient || {};

  const children = [];

  // Sender info
  const senderLines = [p.name, p.email, p.phone, p.location].filter(Boolean);
  for (const line of senderLines) {
    children.push(new Paragraph({
      spacing: { after: 20 },
      children: [new TextRun({ text: line, font, size: bodySize })]
    }));
  }

  children.push(new Paragraph({ spacing: { after: 200 }, children: [] }));

  // Date
  if (content.date) {
    children.push(new Paragraph({
      spacing: { after: 200 },
      children: [new TextRun({ text: content.date, font, size: bodySize })]
    }));
  }

  // Recipient info
  const recipientLines = [r.name, r.title, r.company, r.address].filter(Boolean);
  for (const line of recipientLines) {
    children.push(new Paragraph({
      spacing: { after: 20 },
      children: [new TextRun({ text: line, font, size: bodySize })]
    }));
  }
  if (recipientLines.length > 0) {
    children.push(new Paragraph({ spacing: { after: 200 }, children: [] }));
  }

  // Salutation
  children.push(new Paragraph({
    spacing: { after: 200 },
    children: [new TextRun({ text: content.salutation || 'Dear Hiring Team,', font, size: bodySize })]
  }));

  // Body paragraphs
  if (content.paragraphs) {
    for (const para of content.paragraphs) {
      children.push(new Paragraph({
        spacing: { after: 200, line: 276 },
        children: [new TextRun({ text: para, font, size: bodySize })]
      }));
    }
  }

  // Closing
  children.push(new Paragraph({
    spacing: { before: 200, after: 600 },
    children: [new TextRun({ text: content.closing || 'Sincerely,', font, size: bodySize })]
  }));

  // Signature (name)
  children.push(new Paragraph({
    children: [new TextRun({ text: p.name || '', font, size: bodySize })]
  }));

  return new Document({
    styles: {
      default: { document: { run: { font, size: bodySize } } }
    },
    sections: [{
      properties: {
        page: {
          size: { width: 12240, height: 15840 },
          margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 }
        }
      },
      children
    }]
  });
}

// Main execution
async function main() {
  let doc;
  if (docType === 'cover_letter') {
    doc = generateCoverLetter(content);
  } else {
    doc = generateResume(content);
  }

  const buffer = await Packer.toBuffer(doc);
  const outDir = path.dirname(outputPath);
  if (!fs.existsSync(outDir)) {
    fs.mkdirSync(outDir, { recursive: true });
  }
  fs.writeFileSync(outputPath, buffer);
  console.log(`Generated: ${outputPath} (${(buffer.length / 1024).toFixed(1)} KB)`);
}

main().catch(err => {
  console.error('Error generating document:', err);
  process.exit(1);
});
