import { execSync } from 'child_process';
import { existsSync, readFileSync } from 'fs';
import { resolve, basename } from 'path';
import { getPlatformInfo } from '../utils/platform.js';

export interface ProjectContext {
  cwd: string;
  projectName: string;
  gitBranch?: string;
  gitStatus?: string;
  gitRemote?: string;
  packageManager?: string;
  language?: string;
  framework?: string;
}

export class ContextCollector {
  collect() {
    return {
      platform: getPlatformInfo(),
      project: this.collectProject(),
      timestamp: new Date().toISOString(),
    };
  }

  private collectProject(): ProjectContext {
    const cwd = process.cwd();
    const ctx: ProjectContext = { cwd, projectName: basename(cwd) };

    const tryExec = (cmd: string): string | undefined => {
      try {
        return execSync(cmd, { encoding: 'utf-8', cwd, stdio: ['pipe', 'pipe', 'pipe'] }).trim();
      } catch { return undefined; }
    };

    ctx.gitBranch = tryExec('git branch --show-current');
    ctx.gitStatus = tryExec('git status --porcelain');
    ctx.gitRemote = tryExec('git remote get-url origin');

    // Detect package manager
    if (existsSync(resolve(cwd, 'bun.lockb'))) ctx.packageManager = 'bun';
    else if (existsSync(resolve(cwd, 'pnpm-lock.yaml'))) ctx.packageManager = 'pnpm';
    else if (existsSync(resolve(cwd, 'yarn.lock'))) ctx.packageManager = 'yarn';
    else if (existsSync(resolve(cwd, 'package-lock.json'))) ctx.packageManager = 'npm';

    // Detect language
    if (existsSync(resolve(cwd, 'tsconfig.json'))) ctx.language = 'TypeScript';
    else if (existsSync(resolve(cwd, 'package.json'))) ctx.language = 'JavaScript';
    else if (existsSync(resolve(cwd, 'Cargo.toml'))) ctx.language = 'Rust';
    else if (existsSync(resolve(cwd, 'go.mod'))) ctx.language = 'Go';
    else if (existsSync(resolve(cwd, 'requirements.txt'))) ctx.language = 'Python';

    // Detect framework
    try {
      if (existsSync(resolve(cwd, 'package.json'))) {
        const pkg = JSON.parse(readFileSync(resolve(cwd, 'package.json'), 'utf-8'));
        const deps = { ...pkg.dependencies, ...pkg.devDependencies };
        if (deps['next']) ctx.framework = 'Next.js';
        else if (deps['react']) ctx.framework = 'React';
        else if (deps['vue']) ctx.framework = 'Vue';
        else if (deps['svelte']) ctx.framework = 'Svelte';
        else if (deps['express']) ctx.framework = 'Express';
      }
    } catch {}

    return ctx;
  }

  formatForPrompt(): string {
    const ctx = this.collect();
    const lines = [
      `OS: ${ctx.platform.os}`,
      `Shell: ${ctx.platform.shell}`,
      `CWD: ${ctx.project.cwd}`,
      `Project: ${ctx.project.projectName}`,
    ];
    if (ctx.project.gitBranch) lines.push(`Git: ${ctx.project.gitBranch}`);
    if (ctx.project.language) lines.push(`Lang: ${ctx.project.language}`);
    if (ctx.project.framework) lines.push(`Framework: ${ctx.project.framework}`);
    if (ctx.project.packageManager) lines.push(`PM: ${ctx.project.packageManager}`);
    return lines.join('\n');
  }
}
