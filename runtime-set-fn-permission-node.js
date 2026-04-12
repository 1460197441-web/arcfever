const { spawn } = require('child_process');
const child = spawn('node', [
  'C:/Users/arcfever/AppData/Roaming/npm/node_modules/@cloudbase/cli/bin/tcb',
  'permission',
  'set',
  'function',
  '-e',
  'cloud1-7gjejudlc855f225',
  '--level',
  'custom',
  '--rule',
  '{"*":{"invoke":true}}'
], { stdio: ['pipe', 'pipe', 'pipe'] });
child.stdout.on('data', d => process.stdout.write(d));
child.stderr.on('data', d => process.stderr.write(d));
setTimeout(() => child.stdin.write('y\n'), 500);
child.on('close', code => process.exit(code));