import { readFileSync } from 'node:fs';

export function assertNoMarker(files, marker) {
  for (const file of files) {
    if (readFileSync(file, 'utf8').includes(marker)) {
      throw new Error('secret marker found in release bundle');
    }
  }
}

export function assertNoLiteralSecretAssignments(files) {
  const literalAssignment = /(?:^|[\s,{])["']?(?:VITE_)?LOSTARK_API_TOKEN["']?\s*[:=]\s*["'][^"'\r\n]+["']/m;
  for (const file of files) {
    if (literalAssignment.test(readFileSync(file, 'utf8'))) {
      throw new Error('literal secret assignment found in Worker config');
    }
  }
}
