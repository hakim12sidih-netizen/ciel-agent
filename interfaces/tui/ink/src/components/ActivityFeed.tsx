import React, { useEffect, useState, useRef, useCallback } from 'react';
import { Box, Text, useInput } from 'ink';
import { gateway } from '../gateway/client';
import { useSkin } from './SkinEngine';

interface ActivityItem {
  id: string;
  type: 'tool_progress' | 'tool_complete' | 'tool_error' | 'session_event' | 'system';
  message: string;
  timestamp: number;
  tool?: string;
  progress?: number;
}

interface Props {
  onClose: () => void;
}

export default function ActivityFeed({ onClose }: Props) {
  const [items, setItems] = useState<ActivityItem[]>([]);
  const [filter, setFilter] = useState<string | null>(null);
  const { skin } = useSkin();

  useEffect(() => {
    const unsubProgress = gateway.on('tool.progress', (event: any) => {
      setItems((prev) => [
        {
          id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          type: event.progress >= 100 ? 'tool_complete' : 'tool_progress',
          message: event.message || `${event.tool}: ${event.progress}%`,
          timestamp: Date.now(),
          tool: event.tool,
          progress: event.progress,
        },
        ...prev.slice(0, 99),
      ]);
    });

    const unsubSession = gateway.on('session.changed', (event: any) => {
      setItems((prev) => [
        {
          id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          type: 'session_event',
          message: event.session
            ? `Session ${event.session.id?.slice(0, 8) || 'created'}`
            : 'Session closed',
          timestamp: Date.now(),
        },
        ...prev.slice(0, 99),
      ]);
    });

    return () => {
      unsubProgress();
      unsubSession();
    };
  }, []);

  useInput((_input, key) => {
    if (key.escape || (key.ctrl && key.name === 's')) {
      onClose();
      return;
    }
    // Number keys for filtering
    if (key.ctrl && key.name === 'a') {
      setFilter(null);
      return;
    }
  });

  const typeColor = (type: ActivityItem['type']) => {
    switch (type) {
      case 'tool_progress': return skin.colors.warning;
      case 'tool_complete': return skin.colors.success;
      case 'tool_error': return skin.colors.error;
      case 'session_event': return skin.colors.bannerAccent;
      default: return skin.colors.muted;
    }
  };

  const typeIcon = (type: ActivityItem['type']) => {
    switch (type) {
      case 'tool_progress': return '⟳';
      case 'tool_complete': return '✔';
      case 'tool_error': return '✘';
      case 'session_event': return '◈';
      default: return '·';
    }
  };

  const filtered = filter
    ? items.filter((i) => i.type === filter)
    : items;

  return (
    <Box
      position="absolute"
      right={0}
      top={0}
      width={44}
      flexDirection="column"
      borderStyle="round"
      borderColor={skin.colors.bannerBorder}
      backgroundColor="#000000"
    >
      {/* Header */}
      <Box justifyContent="space-between" paddingX={1} marginBottom={1}>
        <Text color={skin.colors.bannerTitle} bold>
          Activity ({items.length})
        </Text>
        <Text color={skin.colors.muted} dimColor>
          Esc close
        </Text>
      </Box>

      {/* Filter bar */}
      <Box paddingX={1} marginBottom={1}>
        <Text color={skin.colors.muted} dimColor>
          {filter ? `Filter: ${filter.replace('_', ' ')}` : 'All events'}
        </Text>
      </Box>

      {/* Empty state */}
      {filtered.length === 0 && (
        <Box paddingX={1} paddingY={2}>
          <Text color={skin.colors.muted} dimColor>
            {items.length === 0 ? 'No recent activity' : 'No matching events'}
          </Text>
        </Box>
      )}

      {/* Event list */}
      <Box flexDirection="column" flexGrow={1}>
        {filtered.slice(0, 20).map((item) => (
          <Box key={item.id} paddingX={1} paddingY={0}>
            <Text color={typeColor(item.type)}>
              {typeIcon(item.type)}{' '}
            </Text>
            <Text color={skin.colors.muted} dimColor>
              {new Date(item.timestamp).toLocaleTimeString(undefined, {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
              })}
            </Text>
            {' '}
            {item.tool && (
              <Text color={skin.colors.toolOutput} bold>
                {skin.toolEmojis[item.tool] || skin.toolPrefix}{' '}
              </Text>
            )}
            <Text color="#DFE6E9">
              {item.message.length > 36
                ? item.message.slice(0, 36) + '…'
                : item.message}
            </Text>
            {item.progress !== undefined && (
              <Text color={skin.colors.muted} dimColor>
                {' '}[{item.progress}%]
              </Text>
            )}
          </Box>
        ))}
      </Box>
    </Box>
  );
}
