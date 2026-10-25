import { readdir } from 'node:fs/promises';
import { join } from 'node:path';

const teamsRoot = new URL('../teams/', import.meta.url);
const entries = (await readdir(teamsRoot, { withFileTypes: true }))
  .filter((entry) => /^team\d+$/.test(entry.name) && entry.isDirectory())
  .sort((a, b) => Number(a.name.slice(4)) - Number(b.name.slice(4)));

if (entries.length !== 10) throw new Error(`Expected 10 team applications, found ${entries.length}`);
for (const entry of entries) {
  const dir = join(teamsRoot.pathname, entry.name);
  for (const required of ['package.json', 'README.md', '.env.example', 'index.html', 'src/main.js']) {
    try { await import('node:fs/promises').then(({ access }) => access(join(dir, required))); }
    catch { throw new Error(`${entry.name} is missing ${required}`); }
  }
}
console.log(`Validated ${entries.length} independent frontend team applications.`);
