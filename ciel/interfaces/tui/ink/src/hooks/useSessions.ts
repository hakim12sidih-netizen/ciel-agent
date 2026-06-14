import { useCallback } from 'react';
import { gateway } from '../gateway/client';
import {
  currentSession,
  chatActions,
  sessionActions,
  sessions,
} from '../store';
import { useStore } from '@nanostores/react';
import type { SessionInfo } from '../types';

export function useSessions() {
  const session = useStore(currentSession);
  const sessionList = useStore(sessions);

  const createSession = useCallback(async () => {
    try {
      const result = (await gateway.request('sessions.create', {
        source: 'tui',
        platform: 'ink',
        cwd: process.cwd(),
      })) as SessionInfo;
      sessionActions.setCurrent(result);
      sessionActions.addToList(result);
      chatActions.clearMessages();
      return result;
    } catch (err) {
      sessionActions.setError(`Failed to create session: ${(err as Error).message}`);
      return null;
    }
  }, []);

  const selectSession = useCallback(async (sessionId: string) => {
    try {
      const result = (await gateway.request('sessions.get', {
        id: sessionId,
      })) as SessionInfo;
      sessionActions.setCurrent(result);
      // Load last messages (in a real app we'd load them from the session store)
      return result;
    } catch (err) {
      sessionActions.setError(`Failed to load session: ${(err as Error).message}`);
      return null;
    }
  }, []);

  const deleteSession = useCallback(async (sessionId: string) => {
    try {
      await gateway.request('sessions.delete', { id: sessionId });
      sessionActions.removeFromList(sessionId);
      if (session?.id === sessionId) {
        sessionActions.setCurrent(null);
      }
      return true;
    } catch (err) {
      sessionActions.setError(`Failed to delete session: ${(err as Error).message}`);
      return false;
    }
  }, [session]);

  const refreshSessions = useCallback(async () => {
    sessionActions.setLoading(true);
    sessionActions.setError(null);
    try {
      const result = (await gateway.request('sessions.list', {
        limit: 50,
        offset: 0,
        source: 'tui',
      })) as any;
      sessionActions.setList(result.sessions || []);
    } catch (err) {
      sessionActions.setError(`Failed to load sessions: ${(err as Error).message}`);
    } finally {
      sessionActions.setLoading(false);
    }
  }, []);

  return {
    session,
    sessionList,
    createSession,
    selectSession,
    deleteSession,
    refreshSessions,
  };
}
