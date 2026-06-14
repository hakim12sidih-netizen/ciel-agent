import React, { useEffect, useCallback, useState } from 'react';
import { Box } from 'ink';
import Transcript from './components/Transcript';
import Composer from './components/Composer';
import SessionPicker from './components/SessionPicker';
import StatusBar from './components/StatusBar';
import ActivityFeed from './components/ActivityFeed';
import SkinEngine from './components/SkinEngine';
import { useChat } from './hooks/useChat';
import { useSessions } from './hooks/useSessions';
import { useKeyboard, type ViewName } from './hooks/useKeyboard';
import { gateway } from './gateway/client';
import { on } from './gateway/events';
import {
  chatActions,
  messages,
  currentSession,
  sessionActions,
  approvalActions,
  pendingApprovals,
} from './store';
import { useStore } from '@nanostores/react';
import type {
  ChatDeltaEvent,
  ChatReasoningEvent,
  ChatToolCallEvent,
  ChatToolResultEvent,
  ChatCompleteEvent,
  ChatErrorEvent,
  ApprovalRequestEvent,
} from './types';

export default function App() {
  const [view, setView] = useState<ViewName>('chat');
  const { sendMessage, retry, clear } = useChat();
  const { createSession, selectSession } = useSessions();
  const session = useStore(currentSession);
  const msgList = useStore(messages);
  const approvals = useStore(pendingApprovals);

  // Wire gateway events to store
  useEffect(() => {
    const unsubDelta = on.delta((event: ChatDeltaEvent) => {
      chatActions.setCurrentToken(event.token);
    });

    const unsubReasoning = on.reasoning((event: ChatReasoningEvent) => {
      chatActions.setReasoning(event.content);
    });

    const unsubToolCall = on.toolCall((event: ChatToolCallEvent) => {
      chatActions.appendToolCall(event.toolCall);
    });

    const unsubToolResult = on.toolResult((event: ChatToolResultEvent) => {
      chatActions.addMessage({
        role: 'tool',
        content: event.result,
        toolCallId: event.toolCallId,
      });
    });

    const unsubComplete = on.complete((event: ChatCompleteEvent) => {
      chatActions.setStreaming(false);
      chatActions.setCurrentToken('');
      chatActions.setReasoning('');
      chatActions.clearToolCalls();

      if (event.sessionId && !currentSession.get()) {
        sessionActions.setCurrent({
          id: event.sessionId,
          source: 'tui',
          platform: 'ink',
          createdAt: Date.now(),
          updatedAt: Date.now(),
          messageCount: 1,
        });
      }
      chatActions.addMessage(event.message);
    });

    const unsubError = on.error((event: ChatErrorEvent) => {
      chatActions.setStreaming(false);
      chatActions.setCurrentToken('');
      chatActions.setReasoning('');
      chatActions.addMessage({
        role: 'assistant',
        content: `Error: ${event.message}`,
      });
    });

    const unsubApproval = on.approvalRequest((event: ApprovalRequestEvent) => {
      approvalActions.add(event);
    });

    return () => {
      unsubDelta();
      unsubReasoning();
      unsubToolCall();
      unsubToolResult();
      unsubComplete();
      unsubError();
      unsubApproval();
    };
  }, []);

  const handleToggleView = useCallback((v: ViewName) => {
    setView(v);
  }, []);

  useKeyboard(view, {
    onToggleView: handleToggleView,
    onClear: clear,
    onQuit: () => {
      gateway.disconnect().then(() => process.exit(0));
    },
  });

  const handleSelectSession = useCallback(
    async (sessionId: string) => {
      await selectSession(sessionId);
      setView('chat');
    },
    [selectSession],
  );

  const handleNewSession = useCallback(async () => {
    await createSession();
    setView('chat');
  }, [createSession]);

  return (
    <SkinEngine>
      <Box flexDirection="column" height="100%">
        {view === 'chat' && (
          <Box flexDirection="column" flexGrow={1}>
            <Transcript messages={msgList} onRetry={retry} />
            <Composer
              onSubmit={sendMessage}
              onNewSession={handleNewSession}
              onToggleSessions={() => setView('sessions')}
              approvals={approvals}
            />
          </Box>
        )}

        {view === 'sessions' && (
          <SessionPicker
            onSelect={handleSelectSession}
            onNew={handleNewSession}
            onBack={() => setView('chat')}
          />
        )}

        {view === 'activity' && (
          <ActivityFeed onClose={() => setView('chat')} />
        )}

        <StatusBar
          session={session}
          connectionState={gateway.state}
          onToggleActivity={() =>
            setView(view === 'activity' ? 'chat' : 'activity')
          }
          onToggleSessions={() =>
            setView(view === 'sessions' ? 'chat' : 'sessions')
          }
        />
      </Box>
    </SkinEngine>
  );
}
