import { readdir } from 'node:fs/promises';
import { join } from 'node:path';
import { spawn } from 'node:child_process';

const teamsRoot = new URL('../teams/', import.meta.url);
const entries = (await readdir(teamsRoot, { withFileTypes: true }))
  .filter((entry) => /^team\d+$/.test(entry.name) && entry.isDirectory())
  .sort((a, b) => Number(a.name.slice(4)) - Number(b.name.slice(4)));

for (const entry of entries) {
  const dir = join(teamsRoot.pathname, entry.name);
  console.log(`Building ${entry.name}...`);
  await new Promise((resolve, reject) => {
    const child = spawn(process.platform === 'win32' ? 'npm.cmd' : 'npm', ['run', 'build'], { cwd: dir, stdio: 'inherit' });
    child.on('error', reject);
    child.on('exit', (code) => code === 0 ? resolve() : reject(new Error(`${entry.name} build failed with code ${code}`)));
  });
}
