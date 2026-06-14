import React, { useState, useCallback, useEffect, useRef } from 'react';
import { Box, Text, useInput } from 'ink';
import TextInput from 'ink-text-input';
import { useSkin } from './SkinEngine';
import { useStore } from '@nanostores/react';
import { isStreaming } from '../store';
import { gateway } from '../gateway/client';
import type { ApprovalRequestEvent } from '../types';

interface Props {
  onSubmit: (input: string) => void;
  onNewSession: () => void;
  onToggleSessions: () => void;
  approvals: ApprovalRequestEvent[];
}

function ApprovalInput({ approval, onRespond }: {
  approval: ApprovalRequestEvent;
  onRespond: (id: string, response: string) => void;
}) {
  const [cursor, setCursor] = useState(0);
  const options = approval.options || ['allow', 'allow_once', 'reject', 'reject_forever'];

  useEffect(() => {
    const idx = options.indexOf(approval.defaultOption);
    if (idx >= 0) setCursor(idx);
  }, [approval.id]);

  useInput((_input, key) => {
    if (key.leftArrow) {
      setCursor((p) => Math.max(0, p - 1));
    }
    if (key.rightArrow) {
      setCursor((p) => Math.min(options.length - 1, p + 1));
    }
    if (key.return) {
      onRespond(approval.id, options[cursor]);
    }
    if (key.escape) {
      onRespond(approval.id, 'reject');
    }
  });

  return (
    <Box flexDirection="column" borderStyle="round" borderColor="yellow" marginBottom={1} padding={1}>
      <Text bold color="yellow">⚠ Approval Required</Text>
      <Box marginTop={1}>
        <Text>{approval.message}</Text>
      </Box>
      <Box marginTop={1}>
        <Text color="yellow" dimColor>Tool:</Text>
        <Text> {approval.tool}</Text>
      </Box>
      <Box marginTop={1} flexDirection="row">
        {options.map((opt, idx) => (
          <Box key={opt} marginRight={2}>
            <Text color={idx === cursor ? 'cyan' : '#636E72'} bold={idx === cursor}>
              {idx === cursor ? '●' : '○'} {opt}
            </Text>
          </Box>
        ))}
      </Box>
      <Box marginTop={1}>
        <Text color="#636E72" dimColor>
          ← → navigate  ·  Enter select  ·  Esc reject
        </Text>
      </Box>
    </Box>
  );
}

export default function Composer({ onSubmit, onNewSession, onToggleSessions, approvals }: Props) {
  const [input, setInput] = useState('');
  const [history, setHistory] = useState<string[]>([]);
  const [historyIdx, setHistoryIdx] = useState(-1);
  const { skin } = useSkin();
  const streaming = useStore(isStreaming);
  const inputActive = !streaming && approvals.length === 0;

  const handleSubmit = useCallback(
    (value: string) => {
      if (streaming) return;
      const trimmed = value.trim();
      if (!trimmed) return;

      setHistory((prev) => [...prev, trimmed]);
      setHistoryIdx(-1);
      setInput('');
      onSubmit(trimmed);
    },
    [streaming, onSubmit],
  );

  const handleHistoryUp = useCallback(() => {
    if (history.length === 0 || !inputActive) return;
    const newIdx = Math.min(history.length - 1, historyIdx + 1);
    setHistoryIdx(newIdx);
    setInput(history[history.length - 1 - newIdx]);
  }, [history, historyIdx, inputActive]);

  const handleHistoryDown = useCallback(() => {
    if (!inputActive) return;
    if (historyIdx <= 0) {
      setHistoryIdx(-1);
      setInput('');
    } else {
      const newIdx = historyIdx - 1;
      setHistoryIdx(newIdx);
      setInput(history[history.length - 1 - newIdx]);
    }
  }, [history, historyIdx, inputActive]);

  const handleApprovalResponse = useCallback(
    async (id: string, response: string) => {
      try {
        await gateway.request('approvals.respond', { id, response });
      } catch (err) {
        console.error('Approval failed:', err);
      }
    },
    [],
  );

  const placeholder =
    approvals.length > 0
      ? 'Resolve approval above...'
      : streaming
        ? 'Waiting for response...'
        : 'Type a message...';

  const prefixColor = streaming ? skin.colors.muted : skin.colors.bannerAccent;

  return (
    <Box flexDirection="column">
      {/* Approval prompts */}
      {approvals.length > 0 && (
        <Box flexDirection="column" marginX={1}>
          {approvals.map((a) => (
            <ApprovalInput
              key={a.id}
              approval={a}
              onRespond={handleApprovalResponse}
            />
          ))}
        </Box>
      )}

      {/* Input area */}
      <Box
        borderStyle="single"
        borderColor={streaming ? skin.colors.muted : skin.colors.bannerBorder}
        marginLeft={1}
        marginRight={1}
      >
        <Box>
          <Text color={prefixColor} bold>
            {' '}{skin.branding.promptSymbol}{' '}
          </Text>
        </Box>
        <Box flexGrow={1}>
          <TextInput
            value={input}
            onChange={setInput}
            onSubmit={handleSubmit}
            placeholder={placeholder}
            focus={inputActive}
          />
        </Box>
      </Box>

      {/* Status line */}
      <Box marginLeft={2} marginRight={1} marginBottom={0}>
        <Text color="#636E72" dimColor>
          {streaming ? '⟳ streaming' : input ? `${input.length} chars` : '⏎ send'}
        </Text>
        <Box flexGrow={1} />
        {history.length > 0 && (
          <Text color="#636E72" dimColor>
            {historyIdx >= 0
              ? `${historyIdx + 1}/${history.length}`
              : `${history.length} in history`}
          </Text>
        )}
      </Box>
    </Box>
  );
}
