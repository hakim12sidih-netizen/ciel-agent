import React from 'react';
import { Box, Text } from 'ink';
import { useSkin } from './SkinEngine';
import type { SessionInfo, GatewayConnectionState } from '../types';
import { useStore } from '@nanostores/react';
import { isStreaming, currentSessionId } from '../store';

interface Props {
  session: SessionInfo | null;
  connectionState: GatewayConnectionState;
  onToggleActivity: () => void;
  onToggleSessions: () => void;
}

export default function StatusBar({
  session,
  connectionState,
  onToggleActivity,
  onToggleSessions,
}: Props) {
  const { skin } = useSkin();
  const streaming = useStore(isStreaming);
  const sessionId = useStore(currentSessionId);

  const dot = connectionState.connected ? '●' : '○';
  const dotColor = connectionState.connected
    ? skin.colors.success
    : connectionState.connecting
      ? skin.colors.warning
      : skin.colors.error;

  const sid = sessionId ? sessionId.slice(0, 8) : '—';

  return (
    <Box
      height={1}
      backgroundColor={skin.colors.bannerBorder}
      paddingLeft={1}
      paddingRight={1}
      width="100%"
    >
      {/* Left: agent name */}
      <Text color="white" bold>
        {skin.branding.agentName}
      </Text>
      <Text color={dotColor}>{' '}{dot}{' '}</Text>

      {/* Session */}
      <Text color="white" dimColor>
        #{sid}
      </Text>

      {/* Streaming */}
      {streaming && (
        <Text color={skin.colors.bannerAccent}>
          {' '}⟳
        </Text>
      )}

      {/* Spacer */}
      <Box flexGrow={1} />

      {/* Right: keybindings */}
      <Text color="#DFE6E9" dimColor>
        ^P sessions{' '}
      </Text>
      <Text color="#DFE6E9" dimColor>
        ^S activity{' '}
      </Text>
      <Text color="#DFE6E9" dimColor>
        ^L clear{' '}
      </Text>
      <Text color="#DFE6E9" dimColor>
        ^C quit
      </Text>
    </Box>
  );
}
