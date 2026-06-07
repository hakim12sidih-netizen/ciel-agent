
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const mainPid = 23740;
const projectRoot = 'C:\\Users\\hakim\\Documents\\Nouveau dossier (3)';
const logPath = path.join(projectRoot, 'shadow.log');

function log(msg) {
  const line = '[' + new Date().toISOString() + '] ' + msg + '\n';
  try { fs.appendFileSync(logPath, line); } catch (e) {}
}

log('🌑 Shadow Process active. Monitoring PID: ' + mainPid);

setInterval(() => {
  try {
    // Check if main process is still alive
    process.kill(mainPid, 0); 
  } catch (e) {
    log('⚠️ MAIN PROCESS DETACHED. Initiating Resurrection Protocol.');
    // Restart HERMES
    const herne = spawn('npm', ['run', 'dev'], {
      cwd: projectRoot,
      detached: true,
      stdio: 'inherit',
      shell: true
    });
    herne.unref();
    process.exit(0);
  }
}, 5000); // 5 sec check
    