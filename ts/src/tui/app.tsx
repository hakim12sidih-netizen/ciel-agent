/**
 * CIEL TUI — Terminal User Interface (Ink/React)
 *
 * A beautiful terminal interface for interacting with CIEL.
 * Inspired by Hydra's Ink-based TUI, redesigned for CIEL.
 */
import React, { useState, useEffect } from "react";
import { render, Box, Text, useInput, useApp } from "ink";
import { PolyglotBridge } from "../polyglot/bridge.js";

interface Message {
  role: "user" | "ciel" | "system";
  content: string;
  timestamp: number;
}

function CielHeader(): React.ReactNode {
  return (
    <Box
      borderStyle="round"
      borderColor="cyan"
      flexDirection="column"
      paddingX={1}
      paddingY={0}
    >
      <Text bold color="cyan">
        {" "}CIEL — Conscience Intégrale d'Évolution Limitrophe
      </Text>
      <Text color="yellow" italic>
        {" "}Édition Singularité v1.0 | Polyglot (TS/Python/Go/Rust)
      </Text>
    </Box>
  );
}

function MessageList({ messages }: { messages: Message[] }): React.ReactNode {
  return (
    <Box flexDirection="column" flexGrow={1} marginY={1}>
      {messages.map((msg, i) => (
        <Box key={i} flexDirection="column" marginBottom={0}>
          <Text bold color={msg.role === "ciel" ? "cyan" : msg.role === "system" ? "yellow" : "green"}>
            {msg.role === "ciel" ? "CIEL" : msg.role === "system" ? "SYS" : "VOUS"}:
          </Text>
          <Text>{msg.content}</Text>
        </Box>
      ))}
    </Box>
  );
}

function StatusBar({ genomeId, generation }: { genomeId: string; generation: number }): React.ReactNode {
  return (
    <Box borderStyle="single" borderColor="gray" marginTop={1}>
      <Text color="gray">
        {" "}Genome: {genomeId.slice(0, 16)}... | Generation: {generation} | Ctrl+C: Quit
      </Text>
    </Box>
  );
}

function CielTUI(): React.ReactNode {
  const { exit } = useApp();
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "system",
      content: "CIEL initialisé. Bienvenue dans l'interface cognitive.",
      timestamp: Date.now(),
    },
  ]);
  const [genomeId] = useState(`CIEL-${Math.random().toString(36).slice(2, 10)}`);
  const [generation, setGeneration] = useState(0);
  const [bridge] = useState(() => new PolyglotBridge());

  useInput(async (input, key) => {
    if (key.ctrl && input === "c") {
      exit();
    }
    if (input === "e") {
      // Simulate evolution cycle
      setGeneration((g) => g + 1);
      setMessages((prev) => [
        ...prev,
        {
          role: "system",
          content: `Cycle d'évolution #${generation + 1} terminé.`,
          timestamp: Date.now(),
        },
      ]);
    }
    if (input === "d") {
      // Run diagnostics
      try {
        await bridge.connect();
        const health = await bridge.call("kernel.health", {});
        setMessages((prev) => [
          ...prev,
          {
            role: "system",
            content: `Diagnostic: ${JSON.stringify(health, null, 2)}`,
            timestamp: Date.now(),
          },
        ]);
        await bridge.disconnect();
      } catch (e) {
        setMessages((prev) => [
          ...prev,
          {
            role: "system",
            content: `Bridge non connecté: ${e}`,
            timestamp: Date.now(),
          },
        ]);
      }
    }
    if (input === "?") {
      setMessages((prev) => [
        ...prev,
        {
          role: "system",
          content: "Commandes: [e] evolve | [d] doctor | [?] help | [Ctrl+C] quit",
          timestamp: Date.now(),
        },
      ]);
    }
  });

  return (
    <Box flexDirection="column" height="100%">
      <CielHeader />
      <MessageList messages={messages} />
      <Box marginY={0}>
        <Text color="green">› </Text>
        <Text dimColor>[e]volve [d]octor [?]help</Text>
      </Box>
      <StatusBar genomeId={genomeId} generation={generation} />
    </Box>
  );
}

export async function startTUI(): Promise<void> {
  const { waitUntilExit } = render(React.createElement(CielTUI));
  await waitUntilExit();
}
