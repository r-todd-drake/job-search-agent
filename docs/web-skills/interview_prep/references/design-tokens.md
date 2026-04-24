# Design Tokens — Interview Prep Package

All color, typography, spacing, and JS helper function definitions.
Read this file before writing any document generation code.

---

## Color Constants

```javascript
const ACCENT      = "1F3A6B";   // dark navy — headings, table headers, alert borders
const ACCENT_LIGHT = "E8EDF5";  // light blue-grey — tint box fills, table row tints
const RULE_COLOR  = "C0C8D8";   // section divider rule color
const TEXT_PRIMARY   = "2C2C2C";
const TEXT_SECONDARY = "3D3D3D";
const TEXT_MUTED     = "6B7280";
const TEXT_WHITE     = "FFFFFF";
const ROW_ALT     = "F5F7FA";   // alternating table row fill
```

---

## Typography Scale

All font: Arial. Sizes in half-points (docx convention).

| Role | Size | Weight | Color |
|---|---|---|---|
| Document title | 36 | bold | ACCENT |
| h1 section heading | 28 | bold | ACCENT |
| h2 sub-heading | 22 | bold | ACCENT |
| h3 block heading | 20 | bold | TEXT_PRIMARY |
| label (field label) | 16 | bold | TEXT_MUTED — all caps |
| body | 20 | regular | TEXT_PRIMARY |
| body italic | 20 | italic | TEXT_PRIMARY |
| bullet | 20 | regular | TEXT_PRIMARY |
| sub-bullet | 19 | regular | TEXT_SECONDARY |
| table body | 19 | regular | TEXT_PRIMARY |
| table header | 19 | bold | TEXT_WHITE |
| footer/caption | 18 | italic | 9CA3AF |

---

## Page Setup

```javascript
properties: {
  page: {
    size: { width: 12240, height: 15840 },  // US Letter — always explicit
    margin: { top: 1080, right: 1260, bottom: 1080, left: 1260 }
  }
}
```

---

## Numbering Config

Always include all three in the document numbering config:

```javascript
numbering: {
  config: [
    {
      reference: "bullets",
      levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2022",
        alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 480, hanging: 280 } } } }]
    },
    {
      reference: "subbullets",
      levels: [{ level: 0, format: LevelFormat.BULLET, text: "\u2013",
        alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 800, hanging: 280 } } } }]
    },
    {
      reference: "numbered",
      levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.",
        alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 480, hanging: 280 } } } }]
    },
  ]
}
```

---

## Border Helpers

```javascript
const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };

const noBorders = {
  top:    { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
  bottom: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
  left:   { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
  right:  { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
};
```

---

## Helper Functions

Implement all of these before building section content. They are the building blocks.

### Typographic primitives

```javascript
function rule() {
  return new Paragraph({
    border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: RULE_COLOR, space: 1 } },
    spacing: { before: 120, after: 120 },
    children: []
  });
}

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    children: [new TextRun({ text, font: "Arial", size: 28, bold: true, color: ACCENT })]
  });
}

function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 240, after: 80 },
    children: [new TextRun({ text, font: "Arial", size: 22, bold: true, color: ACCENT })]
  });
}

function h3(text) {
  return new Paragraph({
    spacing: { before: 200, after: 60 },
    children: [new TextRun({ text, font: "Arial", size: 20, bold: true, color: "2C2C2C" })]
  });
}

function body(text, opts = {}) {
  return new Paragraph({
    spacing: { before: 60, after: 60 },
    children: [new TextRun({
      text, font: "Arial", size: 20,
      bold: opts.bold || false,
      italics: opts.italic || false,
      color: opts.color || TEXT_PRIMARY
    })]
  });
}

function label(text) {
  return new Paragraph({
    spacing: { before: 120, after: 40 },
    children: [new TextRun({
      text: text.toUpperCase(), font: "Arial", size: 16, bold: true, color: TEXT_MUTED
    })]
  });
}

function bullet(text, opts = {}) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    spacing: { before: 40, after: 40 },
    children: [new TextRun({
      text, font: "Arial", size: 20,
      bold: opts.bold || false,
      italics: opts.italic || false,
      color: TEXT_PRIMARY
    })]
  });
}

function subbullet(text) {
  return new Paragraph({
    numbering: { reference: "subbullets", level: 0 },
    spacing: { before: 30, after: 30 },
    children: [new TextRun({ text, font: "Arial", size: 19, color: TEXT_SECONDARY })]
  });
}

function sp(before = 100, after = 40) {
  return new Paragraph({ spacing: { before, after }, children: [] });
}
```

### Layout containers

```javascript
// Tint box: scripts, framing text, story scripts, key context
function tintBox(paragraphs) {
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [9360],
    rows: [new TableRow({
      children: [new TableCell({
        borders: noBorders,
        shading: { fill: ACCENT_LIGHT, type: ShadingType.CLEAR },
        margins: { top: 120, bottom: 120, left: 180, right: 180 },
        width: { size: 9360, type: WidthType.DXA },
        children: paragraphs
      })]
    })]
  });
}

// Alert box: single highest-signal callout — use at most once per section
function alertBox(paragraphs) {
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [9360],
    rows: [new TableRow({
      children: [new TableCell({
        borders: {
          top:    { style: BorderStyle.SINGLE, size: 4, color: ACCENT },
          bottom: { style: BorderStyle.SINGLE, size: 4, color: ACCENT },
          left:   { style: BorderStyle.SINGLE, size: 12, color: ACCENT },
          right:  { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
        },
        shading: { fill: ACCENT_LIGHT, type: ShadingType.CLEAR },
        margins: { top: 100, bottom: 100, left: 200, right: 160 },
        width: { size: 9360, type: WidthType.DXA },
        children: paragraphs
      })]
    })]
  });
}

// Two-column layout: delivery notes, side-by-side comparisons
// Default split: 4500 left, 4680 right (leaves 180 gap)
function twoCol(leftParas, rightParas, leftW = 4500, rightW = 4680) {
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [leftW, rightW],
    rows: [new TableRow({
      children: [
        new TableCell({
          borders: noBorders,
          width: { size: leftW, type: WidthType.DXA },
          margins: { top: 60, bottom: 60, left: 0, right: 180 },
          children: leftParas
        }),
        new TableCell({
          borders: noBorders,
          width: { size: rightW, type: WidthType.DXA },
          margins: { top: 60, bottom: 60, left: 180, right: 0 },
          children: rightParas
        })
      ]
    })]
  });
}
```

### Story block

```javascript
// Standard STAR story block — use for all stories
// Pass null/undefined for situation and task to omit those labels
function storyBlock(title, tag, situation, task, action, result, ifProbed) {
  return [
    sp(160, 40),
    new Paragraph({
      spacing: { before: 160, after: 60 },
      children: [
        new TextRun({ text: title, font: "Arial", size: 22, bold: true, color: TEXT_PRIMARY }),
        new TextRun({ text: "   ", font: "Arial", size: 20 }),
        new TextRun({ text: tag, font: "Arial", size: 18, italics: true, color: TEXT_MUTED }),
      ]
    }),
    ...situation ? [label("Situation"), body(situation)] : [],
    ...task      ? [label("Task"),      body(task)]      : [],
    label("Action"),
    body(action),
    label("Result"),
    body(result),
    ...ifProbed ? [label("If probed"), body(ifProbed, { italic: true })] : [],
  ];
}
```

### Story routing table

```javascript
// Three-column routing table
// rows: array of [question, leadStory, backupStory]
function routingTable(rows) {
  const headerRow = new TableRow({
    children: ["If they ask...", "Lead with", "Backup"].map((text, i) =>
      new TableCell({
        borders,
        shading: { fill: ACCENT, type: ShadingType.CLEAR },
        margins: { top: 80, bottom: 80, left: 120, right: 120 },
        width: { size: [3800, 2780, 2780][i], type: WidthType.DXA },
        children: [new Paragraph({
          children: [new TextRun({ text, font: "Arial", size: 19, bold: true, color: TEXT_WHITE })]
        })]
      })
    )
  });

  const dataRows = rows.map(([q, lead, backup], i) =>
    new TableRow({
      children: [
        [q, 3800, TEXT_PRIMARY, false],
        [lead, 2780, ACCENT, true],
        [backup, 2780, TEXT_SECONDARY, false]
      ].map(([text, w, color, bold]) =>
        new TableCell({
          borders,
          shading: { fill: i % 2 === 0 ? ROW_ALT : "FFFFFF", type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          width: { size: w, type: WidthType.DXA },
          children: [new Paragraph({
            children: [new TextRun({ text, font: "Arial", size: 19, bold, color })]
          })]
        })
      )
    })
  );

  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [3800, 2780, 2780],
    rows: [headerRow, ...dataRows]
  });
}
```

---

## Usage rules

- `tintBox` — use for: intro scripts, story scripts, gap answer scripts, key framing context, closing scripts. Anything the candidate reads from.
- `alertBox` — use for: single highest-signal strategic callout per section. Never use more than once per section. Never use for routine content.
- `twoCol` — use for: delivery notes vs. strategic notes, background vs. implications, logistics vs. time budget.
- `rule()` — use between major sections only. Not between sub-sections.
- `label()` — use for STAR story field labels, gap structure labels, and metadata fields in the cover block.
- Never use plain unicode bullet characters in text runs. Always use the `bullet()` or `subbullet()` helper with numbering config.
- N-dashes in all body text: use `\u2013`. Never use `\u2014` (m-dash).
- Smart quotes: `\u2018` `\u2019` `\u201C` `\u201D`. Never use straight quotes in body text.
