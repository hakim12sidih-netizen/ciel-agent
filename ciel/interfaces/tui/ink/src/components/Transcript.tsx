import React, { useEffect, useRef, useState } from 'react';
import { Box, Text } from 'ink';
import Spinner from 'ink-spinner';
import { useSkin } from './SkinEngine';
import { useStore } from '@nanostores/react';
import { isStreaming, currentToken, reasoning } from '../store';
import type { ChatMessage, ToolCall } from '../types';

interface Props {
  messages: ChatMessage[];
  onRetry: (index: number) => void;
}

function formatInline(src: string): string {
  return src
    .replace(/\*\*(.+?)\*\*/g, (_, m) => m)
    .replace(/`(.+?)`/g, (_, m) => `'${m}'`);
}

function MessageBlock({ msg, idx, skin, onRetry }: {
  msg: ChatMessage;
  idx: number;
  skin: any;
  onRetry: (idx: number) => void;
}) {
  const c = skin.colors;
  const [showReasoning, setShowReasoning] = useState(false);

  switch (msg.role) {
    case 'user':
      return (
        <Box flexDirection="column" marginBottom={1} paddingX={1}>
          <Text color={c.bannerAccent} bold>
            {'❯ '}
          </Text>
          <Text color={c.bannerText}>{msg.content}</Text>
        </Box>
      );

    case 'assistant': {
      const hasReasoning = !!msg.reasoning && msg.reasoning.length > 0;
      const hasToolCalls = !!msg.toolCalls && msg.toolCalls.length > 0;

      return (
        <Box flexDirection="column" marginBottom={1} paddingX={1}>
          <Box>
            <Text color={c.responseBorder} bold>
              {'◈ '}{skin.branding.responseLabel}{' '}
            </Text>
            {hasReasoning && (
              <Text
                color={c.muted}
                dimColor
                underline={showReasoning}
                onClick={() => setShowReasoning(!showReasoning)}
              >
                {'['}{showReasoning ? '−' : '+'}{' '}
                {'reasoning '}{msg.reasoning!.split(' ').length}{' words]'}
              </Text>
            )}
          </Box>

          {hasReasoning && showReasoning && (
            <Box marginLeft={2} marginTop={1} flexDirection="column">
              <Text color={c.muted} dimColor italic>
                {msg.reasoning}
              </Text>
              <Text color={c.muted} dimColor>
                {'─'.repeat(40)}
              </Text>
            </Box>
          )}

          {hasToolCalls && (
            <Box marginLeft={2} marginTop={1} flexDirection="column">
              {msg.toolCalls!.map((tc, tci) => (
                <Box key={tc.id || tci}>
                  <Text color={c.toolOutput} dimColor>
                    {'🔧 '}{tc.function.name}
                  </Text>
                  <Text color={c.muted} dimColor>
                    {' '}({tc.function.arguments.slice(0, 80)}...)
                  </Text>
                </Box>
              ))}
            </Box>
          )}

          {msg.content && (
            <Box marginLeft={2} marginTop={1}>
              <Text color={c.bannerText} wrap="wrap">
                {formatInline(msg.content)}
              </Text>
            </Box>
          )}

          {idx === 0 && false && (
            <Box marginLeft={2} marginTop={0}>
              <Text color={c.muted} dimColor underline onClick={() => onRetry(idx)}>
                [retry]
              </Text>
            </Box>
          )}
        </Box>
      );
    }

    case 'tool':
      return (
        <Box flexDirection="column" marginBottom={1} marginLeft={3} paddingX={1}>
          <Text color={c.toolOutput} dimColor>
            {skin.toolPrefix} {msg.name || 'tool'}
            {msg.toolCallId ? ` #${msg.toolCallId.slice(0, 8)}` : ''}
          </Text>
          <Text color={c.muted} dimColor wrap="wrap">
            {msg.content.length > 300 ? msg.content.slice(0, 300) + '...' : msg.content || '(empty)'}
          </Text>
        </Box>
      );

    case 'system':
      return (
        <Box marginBottom={1} paddingX={1}>
          <Text color={c.muted} dimColor italic>
            {msg.content}
          </Text>
        </Box>
      );

    default:
      return null;
  }
}

function ReasoningChunk({ text, skin }: { text: string; skin: any }) {
  const [collapsed, setCollapsed] = useState(true);
  return (
    <Box flexDirection="column" marginBottom={1} paddingX={1}>
      <Text
        color={skin.colors.muted}
        dimColor
        underline
        onClick={() => setCollapsed(!collapsed)}
      >
        {'['}{collapsed ? '+' : '−'}{' reasoning...]'}
      </Text>
      {!collapsed && (
        <Text color={skin.colors.muted} dimColor italic>
          {text}
        </Text>
      )}
    </Box>
  );
}

export default function Transcript({ messages, onRetry }: Props) {
  const { skin } = useSkin();
  const streaming = useStore(isStreaming);
  const token = useStore(currentToken);
  const reas = useStore(reasoning);
  const scrollRef = useRef<Box>(null);
  const hasMessages = messages.length > 0;

  // Auto-scroll to bottom on new content
  useEffect(() => {
    if (scrollRef.current && hasMessages) {
      // Ink handles this via flex layout
    }
  }, [messages.length, token, hasMessages]);

  return (
    <Box flexDirection="column" flexGrow={1} overflow="hidden">
      {/* Welcome screen */}
      {!hasMessages && !streaming && (
        <Box flexDirection="column" alignItems="center" justifyContent="center" flexGrow={1}>
          <Text color={skin.colors.bannerTitle} bold>
            {skin.branding.welcome}
          </Text>
          <Box marginTop={1} flexDirection="column" alignItems="center">
            <Text color={skin.colors.muted} dimColor>
              {'· Type a message to start chatting'}
            </Text>
            <Text color={skin.colors.muted} dimColor>
              {'· /help for commands'}
            </Text>
            <Text color={skin.colors.muted} dimColor>
              {'· ^P sessions  · ^S activity  · ^L clear'}
            </Text>
          </Box>
        </Box>
      )}

      {/* Message list */}
      <Box flexDirection="column" flexGrow={1} ref={scrollRef as any}>
        {messages.map((msg, idx) => (
          <MessageBlock
            key={`msg-${idx}-${msg.role}`}
            msg={msg}
            idx={idx}
            skin={skin}
            onRetry={onRetry}
          />
        ))}

        {/* Streaming indicator */}
        {streaming && (
          <Box flexDirection="column" marginBottom={1} paddingX={1}>
            <Box>
              <Text color={skin.colors.responseBorder} bold>
                <Spinner type="dots" />
                {' '}
              </Text>
              <Text color={skin.colors.responseBorder} bold>
                {skin.branding.responseLabel}
              </Text>
            </Box>
            {reas && (
              <Box marginLeft={2} marginTop={1}>
                <ReasoningChunk text={reas} skin={skin} />
              </Box>
            )}
            {token && (
              <Box marginLeft={2} marginTop={1}>
                <Text color={skin.colors.bannerText} wrap="wrap">
                  {token}
                </Text>
              </Box>
            )}
          </Box>
        )}
      </Box>
    </Box>
  );
}
