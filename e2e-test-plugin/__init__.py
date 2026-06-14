from ciel.plugins import PluginBase, PluginManifest


class E2ETestPluginPlugin(PluginBase):
    manifest = PluginManifest(
        name="e2e-test-plugin",
        version="0.1.0",
        description="Plugin e2e-test-plugin for CIEL",
    )

    async def on_load(self):
        print(f"  [green]✓ Plugin {self.manifest.name} chargé[/]")

    async def on_enable(self):
        print(f"  [green]✓ Plugin {self.manifest.name} activé[/]")

    async def on_disable(self):
        print(f"  [yellow]⊘ Plugin {self.manifest.name} désactivé[/]")
