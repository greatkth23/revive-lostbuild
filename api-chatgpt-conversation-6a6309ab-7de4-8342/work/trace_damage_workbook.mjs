import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const workbookPath =
  "C:\\Users\\great\\Downloads\\시즌3 전용 데미지 계산기.xlsx";
const outDir =
  "C:\\Users\\great\\Documents\\Codex\\2026-07-25\\api-chatgpt-conversation-6a6309ab-7de4-8342\\work\\workbook_analysis";

await fs.mkdir(outDir, { recursive: true });
const workbook = await SpreadsheetFile.importXlsx(
  await FileBlob.load(workbookPath),
);

const cells = [
  "BI4",
  "P4",
  "M4",
  "M5",
  "T4",
  "AA4",
  "AA5",
  "AE4",
  "AE5",
  "AH4",
  "BB4",
  "BF4",
  "BF5",
  "BB8",
  "AJ62",
  "AK62",
];
const traces = {};

for (const cell of cells) {
  try {
    traces[cell] = await workbook.trace(`데미지 계산기!${cell}`);
  } catch (error) {
    traces[cell] = { error: String(error) };
  }
}

await fs.writeFile(
  path.join(outDir, "artifact_tool_traces.json"),
  JSON.stringify(traces, null, 2),
  "utf8",
);

console.log(
  JSON.stringify(
    {
      outFile: path.join(outDir, "artifact_tool_traces.json"),
      cells,
    },
    null,
    2,
  ),
);
