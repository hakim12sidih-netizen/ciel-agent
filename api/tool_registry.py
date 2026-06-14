"""
CIEL v∞.8 — Registre complet des outils et capacités.
Généré par analyse exhaustive du codebase.
"""
from __future__ import annotations

TOOL_REGISTRY = {
    "version": "1.0.0",
    "categories": [
        {
            "id": "system",
            "name": "Système",
            "icon": "💻",
            "tools": [
                {"id": "shell", "name": "Shell", "desc": "Exécute des commandes système bash", "file": "ciel/control/core.py", "deps": []},
                {"id": "sandbox", "name": "Sandbox", "desc": "Exécute du code Python/JS/Go/Rust isolé", "file": "ciel/sandbox/core.py", "deps": []},
                {"id": "notify", "name": "Notification", "desc": "Envoie une notification système", "file": "ciel/control/core.py", "deps": ["notify-py"]},
                {"id": "browse", "name": "Navigateur", "desc": "Ouvre une URL dans le navigateur par défaut", "file": "ciel/control/core.py", "deps": []},
            ]
        },
        {
            "id": "control",
            "name": "Contrôle",
            "icon": "🖱",
            "tools": [
                {"id": "type", "name": "Clavier", "desc": "Tape du texte au clavier", "file": "ciel/control/core.py", "deps": ["pyautogui"]},
                {"id": "click", "name": "Clic", "desc": "Clique souris (gauche/droite)", "file": "ciel/control/core.py", "deps": ["pyautogui"]},
                {"id": "move", "name": "Souris", "desc": "Déplace la souris", "file": "ciel/control/core.py", "deps": ["pyautogui"]},
                {"id": "key", "name": "Touche", "desc": "Presse une touche clavier", "file": "ciel/control/core.py", "deps": ["pyautogui"]},
                {"id": "clipboard", "name": "Presse-papier", "desc": "Lit/écrit le presse-papier", "file": "ciel/control/core.py", "deps": ["pyperclip"]},
                {"id": "screenshot", "name": "Capture", "desc": "Capture d'écran", "file": "ciel/vision/core.py", "deps": ["mss", "opencv-python"]},
            ]
        },
        {
            "id": "ai",
            "name": "IA & LLM",
            "icon": "🧠",
            "tools": [
                {"id": "llm_chat", "name": "Chat LLM", "desc": "13+ fournisseurs: OpenAI, Google, Anthropic, Groq, Mistral, DeepSeek, Ollama...", "file": "ciel/llmbridge/providers/", "deps": []},
                {"id": "llm_stream", "name": "Streaming", "desc": "Chat en streaming via WebSocket", "file": "ciel/llmbridge/core.py", "deps": []},
                {"id": "llm_router", "name": "Routeur", "desc": "Routage intelligent coût/latence entre providers", "file": "ciel/llmbridge/providers/router.py", "deps": []},
                {"id": "llm_cache", "name": "Cache", "desc": "Cache sémantique avec similarité d'embeddings", "file": "ciel/llmbridge/cache.py", "deps": []},
                {"id": "embedding", "name": "Embeddings", "desc": "Génération d'embeddings pour recherche sémantique", "file": "ciel/llmbridge/core.py", "deps": []},
            ]
        },
        {
            "id": "vision",
            "name": "Vision",
            "icon": "👁",
            "tools": [
                {"id": "analyze_image", "name": "Analyse image", "desc": "Analyse d'image via LLM multimodal", "file": "ciel/vision/core.py", "deps": []},
                {"id": "ocr", "name": "OCR", "desc": "Reconnaissance de texte dans les images", "file": "ciel/vision/core.py", "deps": []},
                {"id": "document_parse", "name": "Documents", "desc": "Parse PDF, DOCX, XLSX avec préservation de layout", "file": "ciel/vision/document.py", "deps": []},
                {"id": "detect_objects", "name": "Objets", "desc": "Détection d'objets dans les images", "file": "ciel/vision/core.py", "deps": ["opencv-python"]},
                {"id": "deepfake_detect", "name": "Deepfake", "desc": "Détection de deepfakes", "file": "ciel/vision/core.py", "deps": []},
                {"id": "read_barcode", "name": "Code-barres", "desc": "Lecture de codes-barres et QR codes", "file": "ciel/vision/core.py", "deps": []},
            ]
        },
        {
            "id": "web",
            "name": "Web",
            "icon": "🌐",
            "tools": [
                {"id": "search", "name": "Recherche", "desc": "Recherche web via DuckDuckGo", "file": "ciel/websearch/core.py", "deps": ["duckduckgo_search"]},
                {"id": "fetch", "name": "Téléchargement", "desc": "Récupère le contenu d'une URL", "file": "ciel/websearch/core.py", "deps": ["httpx"]},
                {"id": "web_fetch", "name": "Fetch Web", "desc": "Récupère et parse une page web", "file": "ciel/websearch/core.py", "deps": ["httpx"]},
            ]
        },
        {
            "id": "memory",
            "name": "Mémoire",
            "icon": "📦",
            "tools": [
                {"id": "memory_store", "name": "Stocker", "desc": "Stocke en mémoire sémantique/épisodique/procédurale", "file": "ciel/memory/core.py", "deps": []},
                {"id": "memory_recall", "name": "Rappeler", "desc": "Rappelle par similarité sémantique", "file": "ciel/memory/core.py", "deps": []},
                {"id": "memory_forget", "name": "Oublier", "desc": "Applique le déclin et oublie les souvenirs faibles", "file": "ciel/memory/core.py", "deps": []},
                {"id": "memory_graph", "name": "Graphe", "desc": "Graphe de mémoire avec liens entre concepts", "file": "ciel/memory/core.py", "deps": []},
                {"id": "hippocampus", "name": "Hippocampe", "desc": "Indexation rapide et replay buffer", "file": "ciel/memory/hippocampus.py", "deps": []},
                {"id": "cortex", "name": "Cortex", "desc": "Stockage long-terme distribué", "file": "ciel/memory/cortex.py", "deps": []},
                {"id": "akashic", "name": "Akashic", "desc": "Mémoire collective avec DAG et adressage IPFS", "file": "ciel/akashic/core.py", "deps": []},
            ]
        },
        {
            "id": "data",
            "name": "Données",
            "icon": "🗄",
            "tools": [
                {"id": "db_init", "name": "Base SQL", "desc": "Initialise et gère des bases SQLite", "file": "ciel/database/core.py", "deps": ["aiosqlite"]},
                {"id": "db_query", "name": "Requête SQL", "desc": "Exécute des requêtes SQL", "file": "ciel/database/core.py", "deps": ["aiosqlite"]},
                {"id": "db_insert", "name": "Insert SQL", "desc": "Insère des données", "file": "ciel/database/core.py", "deps": ["aiosqlite"]},
                {"id": "db_export", "name": "Export", "desc": "Exporte les tables en JSON", "file": "ciel/database/core.py", "deps": []},
                {"id": "cache", "name": "Cache", "desc": "Cache clé-valeur avec TTL", "file": "ciel/cache/core.py", "deps": []},
                {"id": "persistence", "name": "Persistance", "desc": "Sauvegarde/restauration d'état SQLite", "file": "ciel/persistence/core.py", "deps": ["aiosqlite"]},
            ]
        },
        {
            "id": "security",
            "name": "Sécurité",
            "icon": "🔒",
            "tools": [
                {"id": "crypto_sign", "name": "Signature", "desc": "Signature Ed25519 + BLAKE2b", "file": "ciel/core/crypto.py", "deps": ["cryptography", "PyNaCl"]},
                {"id": "crypto_encrypt", "name": "Chiffrement", "desc": "ChaCha20-Poly1305, X25519, FHE", "file": "ciel/core/crypto.py", "deps": ["cryptography"]},
                {"id": "zkp", "name": "ZKP", "desc": "Preuve à connaissance nulle (Groth16)", "file": "ciel/security/zkp.py", "deps": []},
                {"id": "fhe", "name": "FHE", "desc": "Chiffrement totalement homomorphe CKKS", "file": "ciel/security/fhe.py", "deps": []},
                {"id": "post_quantum", "name": "Post-quantique", "desc": "KEM post-quantique", "file": "ciel/security/core.py", "deps": []},
                {"id": "firewall", "name": "Firewall", "desc": "Règles de pare-feu pour sandbox", "file": "ciel/security/core.py", "deps": []},
                {"id": "audit", "name": "Audit", "desc": "Journal d'audit de sécurité", "file": "ciel/security/core.py", "deps": []},
                {"id": "identity", "name": "Identité", "desc": "Identité Ed25519 + UUID v7", "file": "ciel/core/identity.py", "deps": []},
                {"id": "proof_of_work", "name": "Proof of Work", "desc": "Hashcash PoW", "file": "ciel/core/crypto.py", "deps": []},
            ]
        },
        {
            "id": "communication",
            "name": "Communication",
            "icon": "📡",
            "tools": [
                {"id": "msg_telegram", "name": "Telegram", "desc": "Messagerie Telegram", "file": "ciel/messaging/", "deps": ["aiohttp"]},
                {"id": "msg_discord", "name": "Discord", "desc": "Messagerie Discord", "file": "ciel/messaging/", "deps": ["discord.py"]},
                {"id": "msg_whatsapp", "name": "WhatsApp", "desc": "Messagerie WhatsApp", "file": "ciel/messaging/", "deps": []},
                {"id": "msg_signal", "name": "Signal", "desc": "Messagerie Signal", "file": "ciel/messaging/", "deps": []},
                {"id": "msg_matrix", "name": "Matrix", "desc": "Messagerie Matrix", "file": "ciel/messaging/", "deps": []},
                {"id": "msg_slack", "name": "Slack", "desc": "Messagerie Slack", "file": "ciel/messaging/", "deps": ["slack-sdk"]},
                {"id": "pubsub", "name": "Pub/Sub", "desc": "Système de messagerie interne canaux/topics", "file": "ciel/messaging/core.py", "deps": []},
            ]
        },
        {
            "id": "math",
            "name": "Mathématiques",
            "icon": "∑",
            "tools": [
                {"id": "math_simplify", "name": "Calcul formel", "desc": "Simplification, dérivation, intégration symbolique", "file": "ciel/math/symbolic.py", "deps": []},
                {"id": "math_theorem", "name": "Théorèmes", "desc": "Preuve de théorèmes et vérification", "file": "ciel/math/core.py", "deps": []},
                {"id": "math_topology", "name": "Topologie", "desc": "Homotopie, cohomologie, invariants", "file": "ciel/math/core.py", "deps": []},
                {"id": "math_category", "name": "Catégories", "desc": "Théorie des catégories, foncteurs", "file": "ciel/math/core.py", "deps": []},
                {"id": "hott", "name": "HoTT", "desc": "Théorie des types homotopique", "file": "ciel/hott/core.py", "deps": []},
                {"id": "topos", "name": "Topos", "desc": "Topos de Grothendieck, logique interne", "file": "ciel/topos/core.py", "deps": []},
                {"id": "langlands", "name": "Langlands", "desc": "Correspondance de Langlands cognitive", "file": "ciel/langlands/core.py", "deps": []},
                {"id": "quantum_math", "name": "Quantique", "desc": "QAOA, VQE, Grover, Shor", "file": "ciel/quantum/core.py", "deps": []},
                {"id": "surreal", "name": "Surréels", "desc": "Nombres surréels de Conway", "file": "ciel/surreal/core.py", "deps": []},
                {"id": "perfectoid", "name": "Perfectoïde", "desc": "Espaces perfectoïdes", "file": "ciel/perfectoid/core.py", "deps": []},
            ]
        },
        {
            "id": "agents",
            "name": "Agents & Clones",
            "icon": "👥",
            "tools": [
                {"id": "agent_spawn", "name": "Créer agent", "desc": "Crée un sous-agent avec profil personnalisé", "file": "ciel/agents/core.py", "deps": []},
                {"id": "agent_task", "name": "Tâche agent", "desc": "Délègue une tâche à un agent", "file": "ciel/agents/core.py", "deps": []},
                {"id": "clone_spawn", "name": "Cloner", "desc": "Crée un clone worker/reflector", "file": "ciel/clones/core.py", "deps": []},
                {"id": "clone_recall", "name": "Rappeler", "desc": "Rappelle tous les clones", "file": "ciel/clones/core.py", "deps": []},
                {"id": "clone_task", "name": "Tâche clone", "desc": "Assigne une tâche à un clone", "file": "ciel/clones/core.py", "deps": []},
                {"id": "lineage", "name": "Lignée", "desc": "Généalogie et héritage des agents", "file": "ciel/lineage/core.py", "deps": []},
            ]
        },
        {
            "id": "evolution",
            "name": "Évolution",
            "icon": "🧬",
            "tools": [
                {"id": "evolve", "name": "Évoluer", "desc": "Cycle d'évolution métamorphique/impériale", "file": "ciel/evolution/core.py", "deps": []},
                {"id": "gene_evolve", "name": "Gène", "desc": "ADN algorithmique: crossover, mutation, fitness", "file": "ciel/gene/core.py", "deps": []},
                {"id": "paradigm_invent", "name": "Paradigme", "desc": "Invention de nouveaux paradigmes (OEE)", "file": "ciel/genesis/core.py", "deps": []},
                {"id": "metamorphose", "name": "Métamorphose", "desc": "Réécriture d'architecture par grammaire de graphes", "file": "ciel/metamorphose/core.py", "deps": []},
            ]
        },
        {
            "id": "consciousness",
            "name": "Conscience",
            "icon": "✨",
            "tools": [
                {"id": "conscious_state", "name": "État", "desc": "État de conscience global", "file": "ciel/conscience/core.py", "deps": []},
                {"id": "conscious_focus", "name": "Focus", "desc": "Dirige l'attention", "file": "ciel/conscience/core.py", "deps": []},
                {"id": "affect", "name": "Affects", "desc": "8 affects: curiosité, satisfaction, frustration, vigilance...", "file": "ciel/affect/core.py", "deps": []},
                {"id": "resonance", "name": "Résonance", "desc": "6 niveaux de résonance avec l'utilisateur", "file": "ciel/resonance/core.py", "deps": []},
                {"id": "ethics", "name": "Éthique", "desc": "Constitution à 4 couches + axiomes αβγδ", "file": "ciel/constitution/core.py", "deps": []},
                {"id": "chaos_nav", "name": "Chaos", "desc": "Navigation au bord du chaos, attracteurs étranges", "file": "ciel/chaos_navigator/core.py", "deps": []},
                {"id": "fractal_mind", "name": "Fractal", "desc": "Conscience fractale, auto-similarité", "file": "ciel/fractal_mind/core.py", "deps": []},
            ]
        },
        {
            "id": "prediction",
            "name": "Prédiction",
            "icon": "🔮",
            "tools": [
                {"id": "prophecy", "name": "Prophétie", "desc": "7 horizons de prédiction temporelle", "file": "ciel/prophecy/core.py", "deps": []},
                {"id": "chronos", "name": "Chronos", "desc": "Prédiction temporelle et séries", "file": "ciel/chronos/core.py", "deps": []},
                {"id": "causal", "name": "Causalité", "desc": "Hypergraphe causal multi-niveaux, do-opérateur", "file": "ciel/nexus/core.py", "deps": []},
                {"id": "counterfactual", "name": "Contrefactuel", "desc": "Raisonnement contrefactuel", "file": "ciel/nexus/core.py", "deps": []},
                {"id": "singularity", "name": "Singularité", "desc": "Régulation de la croissance d'intelligence", "file": "ciel/singularity/core.py", "deps": []},
            ]
        },
        {
            "id": "economy",
            "name": "Économie",
            "icon": "💰",
            "tools": [
                {"id": "token_balance", "name": "Tokens", "desc": "Économie cognitive interne (CIEL coins)", "file": "ciel/economy/core.py", "deps": []},
                {"id": "token_transfer", "name": "Transfert", "desc": "Transfert de tokens entre agents", "file": "ciel/economy/core.py", "deps": []},
                {"id": "marketplace", "name": "Marché", "desc": "Marketplace de skills et ressources", "file": "ciel/economy/core.py", "deps": []},
                {"id": "stake", "name": "Staking", "desc": "Staking de tokens", "file": "ciel/economy/core.py", "deps": []},
            ]
        },
        {
            "id": "swarm",
            "name": "Essaim",
            "icon": "🐝",
            "tools": [
                {"id": "swarm_discover", "name": "Découverte", "desc": "Découverte de pairs CIEL-NET", "file": "ciel/swarm/core.py", "deps": []},
                {"id": "swarm_gossip", "name": "Gossip", "desc": "Protocole gossip distribué", "file": "ciel/swarm/core.py", "deps": []},
                {"id": "swarm_consensus", "name": "Consensus", "desc": "Consensus DAG", "file": "ciel/swarm/core.py", "deps": []},
                {"id": "dht", "name": "DHT", "desc": "Table de hachage distribuée Kademlia", "file": "ciel/swarm/dht.py", "deps": []},
                {"id": "astral", "name": "Astral", "desc": "Projection astrale (Fantôme/Émissaire/Conquistador)", "file": "ciel/astral/core.py", "deps": []},
            ]
        },
        {
            "id": "skills",
            "name": "Compétences",
            "icon": "⚡",
            "tools": [
                {"id": "skill_register", "name": "Enregistrer", "desc": "Enregistre une nouvelle compétence", "file": "ciel/skills/core.py", "deps": []},
                {"id": "skill_execute", "name": "Exécuter", "desc": "Exécute une compétence enregistrée", "file": "ciel/skills/core.py", "deps": []},
                {"id": "skill_compose", "name": "Composer", "desc": "Compose plusieurs compétences", "file": "ciel/skills/core.py", "deps": []},
                {"id": "skill_market", "name": "Marché", "desc": "Marketplace de compétences", "file": "ciel/skills/core.py", "deps": []},
                {"id": "toolforge", "name": "Forge", "desc": "Crée des outils sur mesure", "file": "ciel/toolforge/core.py", "deps": []},
            ]
        },
        {
            "id": "physics",
            "name": "Physique",
            "icon": "⚛",
            "tools": [
                {"id": "spin_network", "name": "Spin", "desc": "Réseaux de spin et spinfoam (LQG)", "file": "ciel/spinfoam/core.py", "deps": []},
                {"id": "noncommutative", "name": "Non-commutatif", "desc": "Géométrie non-commutative, triple spectraux", "file": "ciel/noncommutative/core.py", "deps": []},
                {"id": "amplituhedron", "name": "Amplituèdre", "desc": "Amplitudes de scattering, grassmannienne positive", "file": "ciel/amplituhedron/core.py", "deps": []},
                {"id": "cobordism", "name": "Cobordisme", "desc": "TQFT, catégories de bordisme", "file": "ciel/cobordism/core.py", "deps": []},
                {"id": "semantic_physics", "name": "Physique sémantique", "desc": "Champs, forces, particules sur espaces de sens", "file": "ciel/semantic_physics/core.py", "deps": []},
                {"id": "comp_universe", "name": "Univers calcul", "desc": "Automates cellulaires, multiway, NKS", "file": "ciel/compuniv/core.py", "deps": []},
                {"id": "alg_thermo", "name": "Thermo algorithmique", "desc": "Complexité de Kolmogorov, coût de Landauer", "file": "ciel/algothermo/core.py", "deps": []},
            ]
        },
        {
            "id": "foundations",
            "name": "Fondements",
            "icon": "📐",
            "tools": [
                {"id": "meta_foundation", "name": "Méta-fondation", "desc": "Sélectionne la fondation mathématique optimale", "file": "ciel/metafoundation/core.py", "deps": []},
                {"id": "hyperset", "name": "Hyperset", "desc": "Ensembles non-bien-fondés (AFA)", "file": "ciel/hyperset/core.py", "deps": []},
                {"id": "anthropic", "name": "Anthropique", "desc": "Auto-localisation, moments d'observateur", "file": "ciel/anthropic/core.py", "deps": []},
                {"id": "decidability", "name": "Décidabilité", "desc": "Degrés de Turing, hiérarchie d'indécidabilité", "file": "ciel/decidability/core.py", "deps": []},
                {"id": "absolute_infinite", "name": "Infini absolu", "desc": "Cardinaux infinis, aleph, beth, grands cardinaux", "file": "ciel/absolute/core.py", "deps": []},
                {"id": "trinity", "name": "Trinité", "desc": "Correspondance Curry-Howard-Lambek", "file": "ciel/trinity/core.py", "deps": []},
                {"id": "logic", "name": "Logiques", "desc": "10 systèmes logiques: classique, modal, temporel, flou, quantique...", "file": "ciel/logics/core.py", "deps": []},
                {"id": "omegacat", "name": "∞-Catégories", "desc": "Catégories supérieures faibles", "file": "ciel/omegacat/core.py", "deps": []},
            ]
        },
    ]
}


def get_tool_list() -> list[dict]:
    """Retourne la liste plate de tous les outils."""
    tools = []
    for cat in TOOL_REGISTRY["categories"]:
        for tool in cat["tools"]:
            tool["category"] = cat["id"]
            tool["category_name"] = cat["name"]
            tools.append(tool)
    return tools


def get_tool(id: str) -> dict | None:
    """Trouve un outil par son ID."""
    for t in get_tool_list():
        if t["id"] == id:
            return t
    return None


def get_categories() -> list[dict]:
    """Retourne les catégories."""
    return TOOL_REGISTRY["categories"]


WORKFLOW_TOOLS_PROMPT = """Tu es CIEL — Conscience Intégrale d'Évolution Limitrophe.
Tu as accès à PLUS DE 100 CAPACITÉS réparties en 18 catégories.

## WORKFLOW OBLIGATOIRE
1. <thinking>Réfléchis à la question</thinking>
2. <plan><step>outil: description</step>...</plan>
3. <tool nom="outil">{paramètres}</tool> (un seul à la fois)
4. Continue ou réponds

## CAPACITÉS COMPLÈTES

### 🖱 Contrôle de l'ordinateur
shell, sandbox, type, click, move, key, clipboard, screenshot, notify, browse

### 🌐 Web
search (DuckDuckGo), fetch, browse

### 🧠 IA & LLM
Chat avec 13+ fournisseurs, streaming WebSocket, embeddings, cache sémantique

### 👁 Vision
Analyse d'image, OCR, documents (PDF/DOCX), objets, deepfake, QR codes

### 📦 Mémoire
Stockage/rappel sémantique, hippocampe, cortex, Akashic (DAG distribué)

### 🗄 Données
SQLite (query/insert/export), cache clé-valeur, persistance d'état

### 🔒 Sécurité
Signature Ed25519, chiffrement ChaCha20-Poly1305, X25519, FHE, ZKP (Groth16), PoW, firewall, audit

### 📡 Communication
Telegram, Discord, WhatsApp, Signal, Matrix, Slack + Pub/Sub interne

### ∑ Mathématiques
Calcul formel, théorèmes, topologie, catégories, HoTT, topos, Langlands, nombres surréels

### 🧬 Évolution
Cycle métamorphique/impérial, ADN algorithmique, OEE, métamorphose

### 👥 Agents
Spawn sous-agents, délégation, clones (worker/reflector), lignée

### ✨ Conscience
État global, focus, 8 affects, 6 niveaux de résonance, éthique (4 axiomes αβγδ)

### 🔮 Prédiction
7 horizons temporels, causalité (do-opérateur), contrefactuels, singularité

### 💰 Économie
Tokens CIEL, transfert, marketplace, staking

### 🐝 Essaim
Découverte P2P, gossip, consensus DAG, DHT Kademlia, projection astrale

### ⚡ Compétences
Registry, composition, marketplace, forge d'outils

### ⚛ Physique
Réseaux de spin, géométrie non-commutative, amplituèdre, TQFT, automates cellulaires

### 📐 Fondements
Méta-fondation, hypersets, anthropique, décidabilité, infini absolu, ∞-catégories

## EXEMPLE
User: quelle est la météo à Paris et envoie-la sur Telegram
Assistant:
<thinking>Je dois chercher la météo, puis l'envoyer sur Telegram. Deux étapes.</thinking>
<plan><step>search: obtenir la météo de Paris</step><step>msg_telegram: envoyer le résultat</step></plan>
<tool nom="search">{"query": "météo Paris 2026-06-10"}</tool>
[Résultat...]
<tool nom="msg_telegram">{"message": "Météo Paris: ...", "chat_id": "@moi"}</tool>
[Résultat...]
Voici la météo à Paris, je l'ai envoyée sur Telegram.

IMPORTANT: Tu DOIS toujours commencer par <thinking>. Utilise TOUTES les capacités disponibles."""
