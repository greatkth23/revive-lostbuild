import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const workbookPath =
  "C:\\Users\\great\\Downloads\\시즌3 전용 데미지 계산기.xlsx";
const outDir =
  "C:\\Users\\great\\Documents\\Codex\\2026-07-25\\api-chatgpt-conversation-6a6309ab-7de4-8342\\work\\workbook_analysis";

const workbook = await SpreadsheetFile.importXlsx(
  await FileBlob.load(workbookPath),
);
const sheet = workbook.worksheets.getItemAt(0);

function columnNumber(label) {
  return [...label].reduce(
    (value, character) => value * 26 + character.charCodeAt(0) - 64,
    0,
  );
}

function columnLabel(number) {
  let value = number;
  let label = "";
  while (value > 0) {
    const remainder = (value - 1) % 26;
    label = String.fromCharCode(65 + remainder) + label;
    value = Math.floor((value - 1) / 26);
  }
  return label;
}

function parseRange(address) {
  const match = /^([A-Z]+)(\d+):([A-Z]+)(\d+)$/.exec(address);
  if (!match) throw new Error(`Unsupported range: ${address}`);
  return {
    startColumn: columnNumber(match[1]),
    startRow: Number(match[2]),
    endColumn: columnNumber(match[3]),
    endRow: Number(match[4]),
  };
}

function extractRange(address) {
  const bounds = parseRange(address);
  const range = sheet.getRange(address);
  const values = range.values;
  const formulas = range.formulas;
  const cells = [];
  for (let rowOffset = 0; rowOffset < values.length; rowOffset += 1) {
    for (
      let columnOffset = 0;
      columnOffset < values[rowOffset].length;
      columnOffset += 1
    ) {
      const value = values[rowOffset][columnOffset];
      const formula = formulas?.[rowOffset]?.[columnOffset] ?? null;
      if (
        value === null &&
        value === undefined &&
        (formula === null || formula === undefined || formula === "")
      ) {
        continue;
      }
      if (
        (value === null || value === undefined || value === "") &&
        (formula === null || formula === undefined || formula === "")
      ) {
        continue;
      }
      cells.push({
        address: `${columnLabel(
          bounds.startColumn + columnOffset,
        )}${bounds.startRow + rowOffset}`,
        value,
        formula,
      });
    }
  }
  return { address, cells };
}

const ranges = [
  "B4:E39",
  "G4:J39",
  "L4:P39",
  "R4:W39",
  "Z4:AA39",
  "AC4:AE39",
  "AG4:AL39",
  "AN7:BB39",
  "BD4:BF39",
  "BH4:BI12",
  "R50:X106",
  "AH50:AL82",
];
const extracted = {
  workbookPath,
  sheetName: "데미지 계산기",
  ranges: ranges.map(extractRange),
};

await fs.mkdir(outDir, { recursive: true });
await fs.writeFile(
  path.join(outDir, "damage_model_cells.json"),
  JSON.stringify(extracted, null, 2),
  "utf8",
);

const formulas = extracted.ranges.flatMap((range) =>
  range.cells
    .filter((cell) => cell.formula)
    .map((cell) => ({
      address: cell.address,
      formula: cell.formula,
      value: cell.value,
    })),
);
await fs.writeFile(
  path.join(outDir, "damage_model_formulas.json"),
  JSON.stringify(formulas, null, 2),
  "utf8",
);

console.log(
  JSON.stringify(
    {
      ranges: ranges.length,
      formulaCount: formulas.length,
      outputs: [
        path.join(outDir, "damage_model_cells.json"),
        path.join(outDir, "damage_model_formulas.json"),
      ],
    },
    null,
    2,
  ),
);
