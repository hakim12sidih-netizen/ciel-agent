import { useEffect } from 'react';
import { useInput } from 'ink';

export type ViewName = 'chat' | 'sessions' | 'activity';

interface KeyboardBindings {
  onToggleView: (view: ViewName) => void;
  onClear: () => void;
  onQuit: () => void;
}

export function useKeyboard(
  currentView: ViewName,
  { onToggleView, onClear, onQuit }: KeyboardBindings,
) {
  useInput((_input, key) => {
    // Ctrl+C to quit
    if (key.ctrl && key.name === 'c') {
      onQuit();
      return;
    }

    // Ctrl+P to toggle sessions view
    if (key.ctrl && key.name === 'p') {
      onToggleView(currentView === 'chat' ? 'sessions' : 'chat');
      return;
    }

    // Ctrl+S to toggle activity feed
    if (key.ctrl && key.name === 's') {
      onToggleView(currentView === 'activity' ? 'chat' : 'activity');
      return;
    }

    // Ctrl+L to clear
    if (key.ctrl && key.name === 'l') {
      onClear();
      return;
    }

    // Escape to go back to chat
    if (key.escape && currentView !== 'chat') {
      onToggleView('chat');
      return;
    }
  });
}
