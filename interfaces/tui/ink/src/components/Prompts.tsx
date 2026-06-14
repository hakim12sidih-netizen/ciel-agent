import React, { useState, useEffect, useCallback } from 'react';
import { Box, Text, useInput } from 'ink';
import { gateway } from '../gateway/client';
import { useSkin } from './SkinEngine';

interface Props {
  query: string;
  onSelect: (prompt: string) => void;
}

interface Completion {
  type: 'slash' | 'path';
  value: string;
  description?: string;
}

export default function Prompts({ query, onSelect }: Props) {
  const [completions, setCompletions] = useState<Completion[]>([]);
  const [cursor, setCursor] = useState(0);
  const [loading, setLoading] = useState(false);
  const { skin } = useSkin();

  useEffect(() => {
    if (!query) {
      setCompletions([]);
      return;
    }

    const fetchCompletions = async () => {
      setLoading(true);
      try {
        if (query.startsWith('/')) {
          const result = (await gateway.request('completions.slash', {
            query: query.slice(1),
          })) as any;
          setCompletions(
            (result.completions || []).map((c: string) => ({
              type: 'slash',
              value: c,
            })),
          );
        } else if (query.includes('/') || query.includes('.')) {
          const result = (await gateway.request('completions.path', {
            query,
            cwd: process.cwd(),
          })) as any;
          setCompletions(
            (result.completions || []).map((c: string) => ({
              type: 'path',
              value: c,
            })),
          );
        }
      } catch {
        setCompletions([]);
      } finally {
        setLoading(false);
      }
    };

    const timer = setTimeout(fetchCompletions, 200);
    return () => clearTimeout(timer);
  }, [query]);

  useInput((_input, key) => {
    if (key.upArrow) {
      setCursor((prev) => Math.max(0, prev - 1));
      return;
    }
    if (key.downArrow) {
      setCursor((prev) => Math.min(completions.length - 1, prev + 1));
      return;
    }
    if (key.return && completions[cursor]) {
      onSelect(completions[cursor].value);
      return;
    }
  });

  if (completions.length === 0 && !loading) return null;

  return (
    <Box
      flexDirection="column"
      borderStyle="single"
      borderColor={skin.colors.bannerBorder}
      marginLeft={1}
      marginRight={1}
    >
      {loading && (
        <Box paddingX={1}>
          <Text color={skin.colors.muted} dimColor>
            Loading completions...
          </Text>
        </Box>
      )}

      {completions.map((completion, idx) => (
        <Box
          key={completion.value}
          paddingX={1}
          backgroundColor={idx === cursor ? '#6C5CE7' : undefined}
        >
          <Text color={idx === cursor ? 'white' : skin.colors.bannerText}>
            {completion.value}
          </Text>
          {completion.description && (
            <Text color={skin.colors.muted} dimColor>
              {' — '}
              {completion.description}
            </Text>
          )}
        </Box>
      ))}
    </Box>
  );
}
