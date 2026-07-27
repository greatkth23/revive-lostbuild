import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const workbookPath =
  "C:\\Users\\great\\Downloads\\시즌3 전용 데미지 계산기.xlsx";
const outDir =
  "C:\\Users\\great\\Documents\\Codex\\2026-07-25\\api-chatgpt-conversation-6a6309ab-7de4-8342\\work\\workbook_analysis";

await fs.mkdir(outDir, { recursive: true });
const blob = await FileBlob.load(workbookPath);
const workbook = await SpreadsheetFile.importXlsx(blob);

const sheets = await workbook.inspect({
  kind: "sheet",
  include: "id,name",
  maxChars: 20000,
});
const definedNames = await workbook.inspect({
  kind: "definedName",
  include: "name,formula,scope",
  maxChars: 50000,
  options: { maxResults: 1000 },
});

const parseNdjson = (value) =>
  String(value ?? "")
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => JSON.parse(line));
const sheetEntries = parseNdjson(sheets?.ndjson).filter(
  (entry) => entry.kind === "sheet",
);
const sheetNames = sheetEntries
  .map((entry) => entry?.name ?? entry?.sheetName ?? entry?.id)
  .filter(Boolean);

const overview = {
  sheets,
  definedNames,
  sheetEntries,
  sheetNames,
  regions: {},
  formulas: {},
  directRanges: {},
};

for (let index = 0; index < sheetEntries.length; index += 1) {
  const entry = sheetEntries[index];
  const sheetKey = entry.id;
  const usedRange = entry.range ?? entry.address ?? "A1:Z200";
  overview.regions[sheetKey] = await workbook.inspect({
    kind: "region",
    sheetId: sheetKey,
    range: usedRange,
    include: "address,rowCount,columnCount,values,formulas",
    maxChars: 400000,
    options: { maxResults: 50 },
  });
  overview.formulas[sheetKey] = await workbook.inspect({
    kind: "formula",
    sheetId: sheetKey,
    range: usedRange,
    include: "address,formula,value,displayValue",
    maxChars: 500000,
    options: { maxResults: 10000 },
  });
  const worksheet = workbook.worksheets.getItemAt(index);
  const range = worksheet.getRange(usedRange);
  overview.directRanges[sheetKey] = {
    usedRange,
    values: range.values,
    formulas: range.formulas,
    displayFormulas: range.displayFormulas,
    formulaInfos: range.formulaInfos,
  };

  const renderRanges = [
    "A1:O55",
    "P1:AE55",
    "AF1:AU55",
    "AV1:BI55",
    "A56:O106",
    "P56:AE106",
    "AF56:AU106",
    "AV56:BI106",
  ];
  for (let renderIndex = 0; renderIndex < renderRanges.length; renderIndex += 1) {
    const renderRange = renderRanges[renderIndex];
    const rendered = await workbook.render({
      sheetName: entry.name,
      range: renderRange,
      scale: 1.5,
      format: "png",
    });
    await fs.writeFile(
      path.join(
        outDir,
        `sheet_${index + 1}_part_${renderIndex + 1}_${renderRange.replace(
          /:/g,
          "-",
        )}.png`,
      ),
      new Uint8Array(await rendered.arrayBuffer()),
    );
  }
}

await fs.writeFile(
  path.join(outDir, "artifact_tool_overview.json"),
  JSON.stringify(overview, null, 2),
  "utf8",
);

console.log(
  JSON.stringify(
    {
      outDir,
      sheetNames,
      sheetInspectionKeys: Object.keys(sheets ?? {}),
      definedNameInspectionKeys: Object.keys(definedNames ?? {}),
    },
    null,
    2,
  ),
);
