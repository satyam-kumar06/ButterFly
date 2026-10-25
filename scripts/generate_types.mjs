import { readFile, writeFile } from 'node:fs/promises';
import { compile } from 'json-schema-to-typescript';

const root = new URL('../', import.meta.url);
const schema = JSON.parse(await readFile(new URL('docs/schemas/contracts.schema.json', root), 'utf8'));
const output = new URL('apps/web/src/contracts.ts', root);
const types = await compile(schema, 'ContractBundle', {
  bannerComment: '/* Generated from apps/api/contracts.py. Do not edit by hand. */',
  additionalProperties: false,
  unreachableDefinitions: true,
  maxItems: 0,
});
if (process.argv.includes('--check')) {
  if (await readFile(output, 'utf8') !== types) {
    throw new Error('Stale TypeScript contracts. Export schemas and run npm run contracts:types.');
  }
  console.log('TypeScript contracts are current');
} else {
  await writeFile(output, types);
  console.log('Generated apps/web/src/contracts.ts');
}
