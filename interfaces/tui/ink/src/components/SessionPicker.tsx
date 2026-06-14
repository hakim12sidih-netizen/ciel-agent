import React, { useEffect, useState, useCallback } from 'react';
import { Box, Text, useInput } from 'ink';
import { useSessions } from '../hooks/useSessions';
import { useSkin } from './SkinEngine';

interface Props {
  onSelect: (sessionId: string) => void;
  onNew: () => void;
  onBack: () => void;
}

type Mode = 'browse' | 'delete_confirm';

export default function SessionPicker({ onSelect, onNew, onBack }: Props) {
  const [cursor, setCursor] = useState(0);
  const [mode, setMode] = useState<Mode>('browse');
  const { sessionList, session, refreshSessions, deleteSession } = useSessions();
  const { skin } = useSkin();

  useEffect(() => {
    refreshSessions();
  }, []);

  const sorted = [...sessionList].sort(
    (a, b) => (b.updatedAt || 0) - (a.updatedAt || 0),
  );

  const currentId = session?.id;

  useInput((_input, key) => {
    if (key.escape) {
      if (mode === 'delete_confirm') {
        setMode('browse');
        return;
      }
      onBack();
      return;
    }

    if (mode === 'delete_confirm') {
      if (key.return) {
        const target = sorted[cursor];
        if (target) {
          deleteSession(target.id);
        }
        setMode('browse');
      }
      return;
    }

    if (key.upArrow) {
      setCursor((prev) => Math.max(0, prev - 1));
      return;
    }

    if (key.downArrow) {
      setCursor((prev) => Math.min(sorted.length - 1, prev + 1));
      return;
    }

    if (key.return) {
      const target = sorted[cursor];
      if (target) {
        onSelect(target.id);
      }
      return;
    }

    if (key.delete || key.backspace) {
      if (sorted[cursor]) {
        setMode('delete_confirm');
      }
      return;
    }

    if (key.ctrl && key.name === 'n') {
      onNew();
      return;
    }

    if (key.tab) {
      onNew();
      return;
    }

    if (key.ctrl && key.name === 'r') {
      refreshSessions();
      return;
    }
  });

  return (
    <Box flexDirection="column" flexGrow={1} padding={1}>
      {/* Header */}
      <Box justifyContent="space-between" marginBottom={1}>
        <Box>
          <Text color={skin.colors.bannerTitle} bold>
            Sessions
          </Text>
          <Text color={skin.colors.muted} dimColor>
            {' '}({sorted.length})
          </Text>
        </Box>
        <Text color={skin.colors.muted} dimColor>
          {mode === 'delete_confirm'
            ? 'Enter confirm · Esc cancel'
            : '↑↓ nav · Enter select · Del delete · ^N new · ^R refresh · Esc back'}
        </Text>
      </Box>

      {/* Delete confirmation */}
      {mode === 'delete_confirm' && sorted[cursor] && (
        <Box
          borderStyle="round"
          borderColor="red"
          marginBottom={1}
          padding={1}
        >
          <Text color="red" bold>
            Delete session {sorted[cursor].id.slice(0, 8)}?
          </Text>
          <Text color="#636E72" dimColor>
            {' '}({sorted[cursor].title || 'Untitled'}, {sorted[cursor].messageCount} messages)
          </Text>
          <Box marginTop={1}>
            <Text>Enter to confirm · Esc to cancel</Text>
          </Box>
        </Box>
      )}

      {/* Loading */}
      {/* empty state */}
      {sorted.length === 0 && (
        <Box flexDirection="column" alignItems="center" marginTop={4}>
          <Text color={skin.colors.muted} dimColor>
            No sessions yet
          </Text>
          <Text color={skin.colors.bannerAccent} bold marginTop={1}>
            ^N or Tab to create one
          </Text>
        </Box>
      )}

      {/* Session list */}
      {sorted.length > 0 && (
        <Box flexDirection="column">
          {sorted.map((s, idx) => {
            const isActive = s.id === currentId;
            const isCursor = idx === cursor;
            const bg = isCursor ? '#6C5CE7' : undefined;
            const fg = isCursor ? 'white' : isActive ? skin.colors.bannerAccent : skin.colors.bannerText;

            return (
              <Box
                key={s.id}
                paddingX={1}
                paddingY={0}
                backgroundColor={bg}
              >
                <Box width={3}>
                  <Text color={fg}>
                    {isActive ? '●' : isCursor ? '▸' : ' '}
                  </Text>
                </Box>
                <Box width={10}>
                  <Text color={fg}>
                    {s.id.slice(0, 8)}
                  </Text>
                </Box>
                <Box width={20}>
                  <Text color={fg} bold={isActive}>
                    {s.title || s.platform || 'Chat'}
                  </Text>
                </Box>
                <Box width={10}>
                  <Text color={isCursor ? '#DFE6E9' : '#636E72'} dimColor>
                    {s.messageCount} msgs
                  </Text>
                </Box>
                <Box>
                  <Text color={isCursor ? '#DFE6E9' : '#636E72'} dimColor>
                    {new Date(s.updatedAt).toLocaleDateString(undefined, {
                      month: 'short',
                      day: 'numeric',
                    })}
                  </Text>
                </Box>
              </Box>
            );
          })}
        </Box>
      )}
    </Box>
  );
}
