from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

console = Console()


class OnboardWizard:
    """Wizard interactif de configuration CIEL.

    Guide l'utilisateur à travers :
    1. Détection de l'environnement
    2. Configuration des providers LLM
    3. Installation du daemon gateway
    4. Configuration des canaux (Telegram/Discord/Slack)
    5. Génération de l'identité
    """

    def __init__(self):
        self._ciel_dir = Path.home() / ".ciel"
        self._ciel_dir.mkdir(parents=True, exist_ok=True)
        self._config_path = self._ciel_dir / "ciel.json"
        self._config: dict[str, Any] = self._load_config()
        self._steps_completed: list[str] = []

    def _load_config(self) -> dict:
        if self._config_path.exists():
            try:
                return json.loads(self._config_path.read_text())
            except Exception:
                pass
        return {}

    def _save_config(self) -> None:
        self._config_path.write_text(json.dumps(self._config, indent=2, ensure_ascii=False))
        self._mark_step("config_saved")

    def _mark_step(self, step: str) -> None:
        if step not in self._steps_completed:
            self._steps_completed.append(step)

    def run(self) -> bool:
        console.print(Panel(
            "[bold cyan]CIEL — Assistant de configuration[/]\n\n"
            "Bienvenue ! Je vais vous guider à travers la configuration\n"
            "initiale de CIEL. Cela prend environ 2 minutes.\n\n"
            "[dim]Pressez Ctrl+C à tout moment pour annuler.[/]",
            box=box.HEAVY, border_style="cyan",
        ))

        if not Confirm.ask("\nPrêt à commencer ?", default=True):
            console.print("[yellow]Configuration annulée. Vous pouvez relancer 'ciel onboard' plus tard.[/]")
            return False

        self._step_detect_env()
        self._step_providers()
        if Confirm.ask("\nInstaller le gateway (daemon de messagerie) ?", default=True):
            self._step_gateway()
            self._step_channels()
        self._step_identity()
        self._step_finalize()
        return True

    def _step_detect_env(self) -> None:
        console.print("\n[bold cyan]Étape 1/5 : Détection de l'environnement[/]")

        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                      transient=True) as p:
            p.add_task("[cyan]Analyse...", total=None)

            info = {
                "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "platform": sys.platform,
                "docker": shutil.which("docker") is not None,
                "git": shutil.which("git") is not None,
                "pip": shutil.which("pip") is not None,
            }

        table = self._rich_table("Environnement détecté")
        table.add_row("Python", info["python"])
        table.add_row("Plateforme", info["platform"])
        table.add_row("Docker", "✓" if info["docker"] else "✗")
        table.add_row("Git", "✓" if info["git"] else "✗")
        console.print(table)

        self._config["environment"] = info
        self._save_config()
        self._mark_step("detect_env")

    def _step_providers(self) -> None:
        console.print("\n[bold cyan]Étape 2/5 : Configuration des fournisseurs LLM[/]")
        console.print("[dim]CIEL supporte 35+ fournisseurs. Configurez vos clés API.[/]\n")

        if not self._config.get("providers"):
            self._config["providers"] = {}

        providers_config = [
            ("openai", "OPENAI_API_KEY", "OpenAI (GPT-4o, GPT-4, o1, o3)"),
            ("anthropic", "ANTHROPIC_API_KEY", "Anthropic (Claude 3.5 Sonnet, Claude 3 Opus)"),
            ("google", "GOOGLE_API_KEY", "Google (Gemini 2.0 Flash, Gemini 2.0 Pro)"),
            ("deepseek", "DEEPSEEK_API_KEY", "DeepSeek (V3, R1)"),
            ("groq", "GROQ_API_KEY", "Groq (inférence ultra-rapide, Llama, Mixtral)"),
            ("mistral", "MISTRAL_API_KEY", "Mistral AI (Large, Small)"),
            ("perplexity", "PERPLEXITY_API_KEY", "Perplexity (Sonar, recherche + chat)"),
        ]

        for provider_name, env_var, description in providers_config:
            current_key = self._config["providers"].get(provider_name, {}).get("api_key", "")
            current_env = os.environ.get(env_var, "")
            if current_key or current_env:
                masked = "••••" + current_key[-4:] if current_key else "••••" + current_env[-4:]
                console.print(f"  [green]✓[/] {provider_name}: {masked}")
                continue
            if Confirm.ask(f"  Configurer {description} ?", default=False):
                key = Prompt.ask(f"    Clé API {provider_name}", password=True)
                if key:
                    self._config["providers"][provider_name] = {"api_key": key}
                    self._save_config()
                    console.print(f"  [green]✓[/] {provider_name} configuré")

        # Default provider
        if self._config["providers"]:
            current_default = self._config.get("llm", {}).get("default_provider", "")
            default = Prompt.ask(
                "  Fournisseur par défaut",
                default=current_default or list(self._config["providers"].keys())[0],
            )
            if not self._config.get("llm"):
                self._config["llm"] = {}
            self._config["llm"]["default_provider"] = default
            self._save_config()

        self._mark_step("providers")

    def _step_gateway(self) -> None:
        console.print("\n[bold cyan]Étape 3/5 : Installation du daemon Gateway[/]")

        from ciel.gateway.daemon import install, is_systemd_available, is_launchd_available

        if is_systemd_available():
            console.print("  [green]✓ systemd détecté[/]")
        elif is_launchd_available():
            console.print("  [green]✓ launchd détecté[/]")
        else:
            console.print("  [yellow]⚠ Aucun gestionnaire de service trouvé (mode foreground)[/]")

        if Confirm.ask("  Installer le gateway comme service ?", default=True):
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                          transient=True) as p:
                p.add_task("[cyan]Installation...", total=None)
                result = install()
            if result:
                console.print("  [green]✓ Gateway installé comme service système[/]")
            else:
                console.print("  [yellow]⚠ Installation du service ignorée (mode foreground)[/]")

        self._mark_step("gateway")

    def _step_channels(self) -> None:
        console.print("\n[bold cyan]Étape 4/5 : Configuration des canaux de messagerie[/]")

        if not self._config.get("channels"):
            self._config["channels"] = {}

        channels_config = [
            ("telegram", "CIEL_TELEGRAM_TOKEN", "Token bot Telegram (123456:ABC-DEF...)"),
            ("discord", "CIEL_DISCORD_TOKEN", "Token bot Discord"),
            ("slack", "CIEL_SLACK_TOKEN", "Token Slack (xoxb-...)"),
        ]

        for channel_name, env_var, description in channels_config:
            current_token = self._config["channels"].get(channel_name, {}).get("token", "")
            current_env = os.environ.get(env_var, "")
            if current_token or current_env:
                masked = "••••" + current_token[-4:] if current_token else "✓ via env"
                console.print(f"  [green]✓[/] {channel_name}: {masked}")
                continue
            if Confirm.ask(f"  Configurer {description} ?", default=False):
                token = Prompt.ask(f"    Token {channel_name}", password=True)
                if token:
                    self._config["channels"][channel_name] = {"token": token, "enabled": True}
                    self._save_config()
                    console.print(f"  [green]✓[/] {channel_name} configuré")

        self._mark_step("channels")

    def _step_identity(self) -> None:
        console.print("\n[bold cyan]Étape 5/5 : Identité CIEL[/]")

        identity_file = self._ciel_dir / "identity.pub"
        if identity_file.exists():
            console.print(f"  [green]✓ Identité existante : {identity_file.read_text().strip()[:64]}...[/]")
            self._mark_step("identity")
            return

        if Confirm.ask("  Générer une nouvelle identité cryptographique ?", default=True):
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                          transient=True) as p:
                p.add_task("[cyan]Génération...", total=None)
                try:
                    from ciel.core.identity import bootstrap, exists, load
                    p = self._ciel_dir / "identity"
                    i = bootstrap(p)
                    console.print(f"  [green]✓ Identité créée : {i.uuid}[/]")
                except ImportError:
                    subprocess.run(
                        [sys.executable, "-m", "ciel.core.identity", "--create"],
                        cwd=str(self._ciel_dir), capture_output=True,
                    )
                    console.print("  [green]✓ Identité générée[/]")
            self._mark_step("identity")
        else:
            console.print("  [yellow]⚠ Identité non générée[/]")

    def _step_finalize(self) -> None:
        console.print("\n[bold green]Configuration terminée ![/]")
        summary = self.summary()
        console.print(Panel(summary, title="Résumé", border_style="green", box=box.ROUNDED))
        console.print("\n[cyan]Prochaines étapes :[/]")
        console.print("  [dim]•[/] Lancer CIEL : [bold]ciel[/]")
        console.print("  [dim]•[/] Chat interactif : [bold]ciel chat[/]")
        console.print("  [dim]•[/] Démarrer le gateway : [bold]ciel gateway start[/]")
        console.print("  [dim]•[/] Voir les providers : [bold]ciel providers[/]")
        console.print("  [dim]•[/] Diagnostic : [bold]ciel doctor[/]")
        console.print("\n[dim]Pour reconfigurer : ciel onboard[/]")

    def summary(self) -> str:
        lines = []
        providers = self._config.get("providers", {})
        channels = self._config.get("channels", {})

        lines.append(f"  Providers : {len(providers)} configuré(s)")
        for p in providers:
            lines.append(f"    • {p}")
        if not providers:
            lines.append("    [yellow]Aucun[/]")

        lines.append(f"  Canaux : {len(channels)} configuré(s)")
        for c in channels:
            lines.append(f"    • {c}")
        if not channels:
            lines.append("    [yellow]Aucun[/]")

        lines.append(f"  Gateway : {'installé' if 'gateway' in self._steps_completed else 'non installé'}")
        lines.append(f"  Identité : {'✓' if 'identity' in self._steps_completed else '✗'}")
        lines.append(f"  Config : {self._config_path}")

        return "\n".join(lines)

    def _rich_table(self, title: str) -> Any:
        from rich.table import Table
        table = Table(title=title, box=box.ROUNDED)
        table.add_column("Propriété", style="cyan")
        table.add_column("Valeur", style="green")
        return table


def run_onboard() -> bool:
    wizard = OnboardWizard()
    return wizard.run()
