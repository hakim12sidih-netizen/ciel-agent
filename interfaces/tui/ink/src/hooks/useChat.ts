import { useCallback, useEffect, useRef } from 'react';
import { gateway } from '../gateway/client';
import { on } from '../gateway/events';
import {
  chatActions,
  currentSession,
  messages,
  pendingToolCalls,
} from '../store';
import { useStore } from '@nanostores/react';
import type { ChatMessage, ToolCall } from '../types';

export function useChat() {
  const msgList = useStore(messages);
  const session = useStore(currentSession);
  const toolCalls = useStore(pendingToolCalls);
  const bufferRef = useRef({ content: '', reasoning: '' });

  const sendMessage = useCallback(
    async (input: string) => {
      const trimmed = input.trim();
      if (!trimmed) return;

      // Handle slash commands locally
      if (trimmed.startsWith('/')) {
        const handled = handleSlashCommand(trimmed);
        if (handled) return;
      }

      chatActions.addMessage({ role: 'user', content: trimmed });
      chatActions.setStreaming(true);
      chatActions.setCurrentToken('');
      chatActions.setReasoning('');
      bufferRef.current = { content: '', reasoning: '' };

      try {
        await gateway.request('chat.stream', {
          messages: buildContext(msgList, trimmed),
          sessionId: session?.id,
        });
      } catch (err) {
        chatActions.setStreaming(false);
        chatActions.addMessage({
          role: 'assistant',
          content: `Error: ${(err as Error).message}`,
        });
      }
    },
    [session, msgList],
  );

  const retry = useCallback(
    (index: number) => {
      const msgs = msgList.slice(0, index);
      chatActions.clearMessages();
      for (const m of msgs) {
        chatActions.addMessage(m);
      }
    },
    [msgList],
  );

  const clear = useCallback(() => {
    chatActions.clearMessages();
  }, []);

  return { sendMessage, retry, clear, toolCalls };
}

function buildContext(messages: ChatMessage[], newInput: string): ChatMessage[] {
  // Take last 20 messages for context, exclude tool results that are too long
  const recent = messages.filter((m) => {
    if (m.role === 'tool' && m.content.length > 2000) return false;
    return true;
  }).slice(-20);

  return [...recent, { role: 'user' as const, content: newInput }];
}

function handleSlashCommand(input: string): boolean {
  const parts = input.slice(1).split(' ');
  const cmd = parts[0].toLowerCase();

  switch (cmd) {
    case 'clear':
    case 'new':
      chatActions.clearMessages();
      return true;
    case 'help':
      chatActions.addMessage({
        role: 'assistant',
        content: [
          '**Available commands:**',
          '',
          '  `/help`     — Show this help',
          '  `/clear`    — Clear conversation',
          '  `/new`      — Start new session',
          '  `/sessions` — Open session picker',
          '  `/models`   — List available models',
          '  `/providers` — List providers',
          '  `/config`   — Show configuration',
          '  `/status`   — System status',
        ].join('\n'),
      });
      return true;
    default:
      chatActions.addMessage({
        role: 'assistant',
        content: `Unknown command: \`/${cmd}\`. Try \`/help\`.`,
      });
      return true;
  }
}
