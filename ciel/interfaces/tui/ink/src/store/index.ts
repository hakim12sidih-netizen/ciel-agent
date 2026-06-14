import { atom, computed, map, action } from 'nanostores';
import type {
  SessionInfo,
  ChatMessage,
  ToolCall,
  ApprovalRequestEvent,
  SkinConfig,
} from '../types';

// Session Store
export const currentSession = atom<SessionInfo | null>(null);
export const sessions = atom<SessionInfo[]>([]);
export const sessionsLoading = atom(false);
export const sessionsError = atom<string | null>(null);

export const sessionActions = {
  setCurrent: action(currentSession, 'setCurrent', (store, session: SessionInfo | null) => {
    store.set(session);
  }),

  setList: action(sessions, 'setList', (store, list: SessionInfo[]) => {
    store.set(list);
  }),

  addToList: action(sessions, 'addToList', (store, session: SessionInfo) => {
    const updated = [session, ...store.get()];
    store.set(updated);
  }),

  removeFromList: action(sessions, 'removeFromList', (store, id: string) => {
    const updated = store.get().filter((s) => s.id !== id);
    store.set(updated);
  }),

  setLoading: action(sessionsLoading, 'setLoading', (store, loading: boolean) => {
    store.set(loading);
  }),

  setError: action(sessionsError, 'setError', (store, error: string | null) => {
    store.set(error);
  }),
};

// Chat Store
export const messages = atom<ChatMessage[]>([]);
export const isStreaming = atom(false);
export const currentToken = atom('');
export const reasoning = atom('');
export const pendingToolCalls = atom<ToolCall[]>([]);

export const chatActions = {
  addMessage: action(messages, 'addMessage', (store, msg: ChatMessage) => {
    store.set([...store.get(), msg]);
  }),

  clearMessages: action(messages, 'clearMessages', (store) => {
    store.set([]);
    currentToken.set('');
    reasoning.set('');
    pendingToolCalls.set([]);
  }),

  updateLastAssistant: action(messages, 'updateLastAssistant', (store, content: string) => {
    const msgs = [...store.get()];
    for (let i = msgs.length - 1; i >= 0; i--) {
      if (msgs[i].role === 'assistant') {
        msgs[i] = { ...msgs[i], content };
        store.set(msgs);
        return;
      }
    }
  }),

  appendToolCall: action(pendingToolCalls, 'appendToolCall', (store, tc: ToolCall) => {
    store.set([...store.get(), tc]);
  }),

  clearToolCalls: action(pendingToolCalls, 'clearToolCalls', (store) => {
    store.set([]);
  }),

  setStreaming: action(isStreaming, 'setStreaming', (store, v: boolean) => {
    store.set(v);
  }),

  setCurrentToken: action(currentToken, 'setCurrentToken', (store, v: string) => {
    store.set(v);
  }),

  setReasoning: action(reasoning, 'setReasoning', (store, v: string) => {
    store.set(v);
  }),
};

// UI Store
export const uiStore = map({
  skin: null as SkinConfig | null,
  sidebarOpen: false,
  activityFeedOpen: false,
  statusBarVisible: true,
  commandPaletteOpen: false,
});

export const uiActions = {
  setSkin: action(uiStore, 'setSkin', (store, skin: SkinConfig) => {
    store.setKey('skin', skin);
  }),

  toggleSidebar: action(uiStore, 'toggleSidebar', (store) => {
    store.setKey('sidebarOpen', !store.get().sidebarOpen);
  }),

  toggleActivityFeed: action(uiStore, 'toggleActivityFeed', (store) => {
    store.setKey('activityFeedOpen', !store.get().activityFeedOpen);
  }),

  toggleCommandPalette: action(uiStore, 'toggleCommandPalette', (store) => {
    store.setKey('commandPaletteOpen', !store.get().commandPaletteOpen);
  }),

  setStatusBar: action(uiStore, 'setStatusBar', (store, visible: boolean) => {
    store.setKey('statusBarVisible', visible);
  }),
};

// Pending Approvals
export const pendingApprovals = atom<ApprovalRequestEvent[]>([]);

export const approvalActions = {
  add: action(pendingApprovals, 'add', (store, approval: ApprovalRequestEvent) => {
    store.set([...store.get(), approval]);
  }),

  remove: action(pendingApprovals, 'remove', (store, id: string) => {
    store.set(store.get().filter((a) => a.id !== id));
  }),

  clear: action(pendingApprovals, 'clear', (store) => {
    store.set([]);
  }),
};

// Computed
export const hasActiveStream = computed(isStreaming, (v) => v);
export const currentSessionId = computed(currentSession, (s) => s?.id ?? null);
export const sessionMessageCount = computed(currentSession, (s) => s?.messageCount ?? 0);
