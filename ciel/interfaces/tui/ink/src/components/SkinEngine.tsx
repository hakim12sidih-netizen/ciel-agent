import React, { createContext, useContext, useEffect, ReactNode } from 'react';
import { uiActions } from '../store';
import { gateway } from '../gateway/client';
import type { SkinConfig } from '../types';

const DEFAULT_SKIN: SkinConfig = {
  name: 'ciel-dark',
  description: 'CIEL Dark Theme',
  colors: {
    bannerBorder: '#6C5CE7',
    bannerTitle: '#A29BFE',
    bannerAccent: '#FD79A8',
    bannerDim: '#636E72',
    bannerText: '#DFE6E9',
    responseBorder: '#74B9FF',
    toolOutput: '#55E6C1',
    error: '#FF6B6B',
    warning: '#FECA57',
    success: '#55E6C1',
    muted: '#636E72',
  },
  spinner: {
    waitingFaces: ['(⌐■_■)', '(¬_¬)', '(•_•)', '(◕‿◕)'],
    thinkingFaces: ['(⊙_⊙)', '(◉_◉)', '(◎_◎)', '(◉‿◉)'],
    thinkingVerbs: [
      'contemplating', 'synthesizing', 'analyzing', 'processing',
      'reasoning', 'computing', 'optimizing', 'evolving',
    ],
    wings: [
      ['★', '✧', '✦', '✧', '★'],
      ['✧', '✦', '★', '✦', '✧'],
    ],
  },
  branding: {
    agentName: 'CIEL',
    welcome: 'Hello, I\'m CIEL',
    responseLabel: 'CIEL',
    promptSymbol: '❯',
  },
  toolPrefix: '🔧',
  toolEmojis: {
    bash: '💻',
    read: '📖',
    write: '✍️',
    glob: '🔍',
    grep: '🔎',
    web_search: '🌐',
    web_fetch: '📄',
    edit: '✏️',
    ask: '❓',
    computer: '🖥️',
    voice: '🎤',
    mcp: '🔌',
  },
};

interface SkinContextType {
  skin: SkinConfig;
}

const SkinContext = createContext<SkinContextType>({ skin: DEFAULT_SKIN });

export function useSkin() {
  return useContext(SkinContext);
}

interface Props {
  children: ReactNode;
}

export default function SkinEngine({ children }: Props) {
  useEffect(() => {
    const skin = gateway.getSkin() || DEFAULT_SKIN;
    uiActions.setSkin(skin);
  }, []);

  return (
    <SkinContext.Provider value={{ skin: gateway.getSkin() || DEFAULT_SKIN }}>
      {children}
    </SkinContext.Provider>
  );
}
