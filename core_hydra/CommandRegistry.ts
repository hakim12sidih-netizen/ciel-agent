import type { Command } from '../commands/Command.js';

export class CommandRegistry {
  private commands: Map<string, Command> = new Map();
  private aliases: Map<string, string> = new Map();

  register(command: Command) {
    this.commands.set(command.name, command);
    if (command.aliases) {
      for (const alias of command.aliases) {
        this.aliases.set(alias, command.name);
      }
    }
  }

  get(nameOrAlias: string): Command | undefined {
    const canonicalName = this.aliases.get(nameOrAlias) || nameOrAlias;
    return this.commands.get(canonicalName);
  }

  getAll(): Command[] {
    return Array.from(this.commands.values());
  }

  getHelpText(): string {
    const visibleCommands = this.getAll().filter(c => !c.hidden).sort((a, b) => a.name.localeCompare(b.name));
    
    let help = '━━━ HYDRA Commands ━━━\n';
    
    for (const cmd of visibleCommands) {
      const aliasStr = cmd.aliases ? ` (${cmd.aliases.join(', ')})` : '';
      help += `/${cmd.name.padEnd(12)}${aliasStr.padEnd(12)} — ${cmd.description}\n`;
    }
    
    help += '━━━━━━━━━━━━━━━━━━━━━━━\n';
    help += 'MANDATORY HYDRA WORKFLOW:\n';
    help += '1) Décomposition (Chain-of-Thought)\n';
    help += '   - Diviser en sous-problèmes atomiques\n';
    help += '2) Analyse (exigences, entrées)\n';
    help += '3) Modélisation (structures de données)\n';
    help += '4) Contraintes (complexité, limites)\n';
    help += '5) Conception algorithmique (DP, Greedy, Graphes)\n';
    help += '6) Pseudo-code + preuve de correction\n';
    help += '7) Implémentation\n';
    help += '8) Bonnes pratiques (SOLID, DRY, KISS)\n';
    help += '9) Code propre (noms, commentaires)\n';
    help += '10) Tests & validation (TDD, unitaires, intégration, E2E)\n';
    help += '11) Optimisation & profiling\n';
    help += '12) Revue & réflexion critique\n';
    help += '13) CI/CD & déploiement\n';
    help += '14) Apprentissage continu\n';
    return help;
  }
}
