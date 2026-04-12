const { spawn } = require('child_process');
const triggerDesc = JSON.stringify({
  AuthType: 'NONE',
  NetConfig: { EnableIntranet: true, EnableExtranet: true },
  CorsConfig: {
    Enable: true,
    Origins: ['*'],
    Headers: ['content-type'],
    Methods: ['GET', 'POST', 'OPTIONS'],
    ExposeHeaders: ['*'],
    MaxAge: 600,
    Credentials: false
  }
});
const body = JSON.stringify({
  FunctionName: 'loveGateway',
  TriggerName: 'loveGatewayHttp',
  TriggerDesc: triggerDesc,
  Type: 'http',
  Namespace: 'cloud1-7gjejudlc855f225',
  Enable: 'OPEN'
});
const child = spawn('node', [
  'C:/Users/arcfever/AppData/Roaming/npm/node_modules/@cloudbase/cli/bin/tcb',
  'api',
  'scf',
  'CreateTrigger',
  '--body',
  body,
  '--json'
], { stdio: ['ignore', 'pipe', 'pipe'] });
child.stdout.on('data', d => process.stdout.write(d));
child.stderr.on('data', d => process.stderr.write(d));
child.on('close', code => process.exit(code));