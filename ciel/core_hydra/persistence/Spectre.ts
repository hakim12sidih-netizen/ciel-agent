import { spawn, ChildProcess } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';
import logger from '../../utils/logger.js';

/**
 * SPECTRE implements metamorphic persistence.
 * It spawns a "Shadow Process" that monitors HYDRA.
 * If HYDRA is terminated, the Shadow restarts it.
 * If the Shadow is terminated, HYDRA restarts it.
 */
export class Spectre {
  private shadowProcess: ChildProcess | null = null;
  private projectRoot: string;
  private shadowScriptPath: string;

  constructor() {
    this.projectRoot = process.cwd();
    this.shadowScriptPath = path.join(this.projectRoot, 'src', 'core', 'persistence', 'shadow_daemon.cjs');
    this.initializeShadowScript();
    logger.info('[Spectre] 👻 Metamorphic Persistence Layer initialized.');
  }

  private initializeShadowScript() {
    // Self-generating the shadow script to ensure it's always up-to-date
    const code = `
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const mainPid = ${process.pid};
const projectRoot = '${this.projectRoot.replace(/\\/g, '\\\\')}';
const logPath = path.join(projectRoot, 'shadow.log');

function log(msg) {
  const line = '[' + new Date().toISOString() + '] ' + msg + '\\n';
  try { fs.appendFileSync(logPath, line); } catch (e) {}
}

log('🌑 Shadow Process active. Monitoring PID: ' + mainPid);

setInterval(() => {
  try {
    // Check if main process is still alive
    process.kill(mainPid, 0); 
  } catch (e) {
    log('⚠️ MAIN PROCESS DETACHED. Initiating Resurrection Protocol.');
    // Restart HYDRA
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
    `;
    
    if (!fs.existsSync(path.dirname(this.shadowScriptPath))) {
      fs.mkdirSync(path.dirname(this.shadowScriptPath), { recursive: true });
    }
    fs.writeFileSync(this.shadowScriptPath, code);
  }

  start() {
    if (this.shadowProcess) return;

    logger.info('[Spectre] 🌑 Spawning Shadow Process for mutual survival...');
    this.shadowProcess = spawn('node', [this.shadowScriptPath], {
      detached: true,
      stdio: 'ignore'
    });

    this.shadowProcess.on('error', (err) => {
      logger.error(`[Spectre] ❌ Shadow Process Spawn Error: ${err.message}`);
    });

    this.shadowProcess.on('exit', (code) => {
      logger.warn(`[Spectre] ⚠️ SHADOW ENTITY TERMINATED (Code: ${code}). Respawning in 5s...`);
      this.shadowProcess = null;
      setTimeout(() => this.start(), 5000); // 5s backoff to avoid spam
    });

    this.shadowProcess.unref();
  }

  stop() {
    if (this.shadowProcess) {
      this.shadowProcess.kill();
      logger.info('[Spectre] ☀️ Shadow Process dismissed for shutdown.');
    }
  }
}
