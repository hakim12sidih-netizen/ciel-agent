import { gateway } from './client';
import type {
  GatewayEvent,
  ChatDeltaEvent,
  ChatReasoningEvent,
  ChatToolCallEvent,
  ChatToolResultEvent,
  ChatCompleteEvent,
  ChatErrorEvent,
  ApprovalRequestEvent,
  SessionChangedEvent,
  ToolProgressEvent,
} from '../types';

type EventCallback<T> = (event: T) => void;

interface EventSubscriptions {
  delta: Set<EventCallback<ChatDeltaEvent>>;
  reasoning: Set<EventCallback<ChatReasoningEvent>>;
  toolCall: Set<EventCallback<ChatToolCallEvent>>;
  toolResult: Set<EventCallback<ChatToolResultEvent>>;
  complete: Set<EventCallback<ChatCompleteEvent>>;
  errorEvents: Set<EventCallback<ChatErrorEvent>>;
  sessionChanged: Set<EventCallback<SessionChangedEvent>>;
  toolProgress: Set<EventCallback<ToolProgressEvent>>;
  approvalRequest: Set<EventCallback<ApprovalRequestEvent>>;
}

const subscriptions: EventSubscriptions = {
  delta: new Set(),
  reasoning: new Set(),
  toolCall: new Set(),
  toolResult: new Set(),
  complete: new Set(),
  errorEvents: new Set(),
  sessionChanged: new Set(),
  toolProgress: new Set(),
  approvalRequest: new Set(),
};

const eventToSubscriptionMethod: Record<string, keyof EventSubscriptions> = {
  delta: 'delta',
  reasoning: 'reasoning',
  tool_call: 'toolCall',
  tool_result: 'toolResult',
  complete: 'complete',
  error: 'errorEvents',
  'session.changed': 'sessionChanged',
  'tool.progress': 'toolProgress',
  approval_request: 'approvalRequest',
};

let initialized = false;

export function initEventBus() {
  if (initialized) return;
  initialized = true;

  gateway.on('*', (event: GatewayEvent) => {
    const subKey = eventToSubscriptionMethod[(event as any).method || event.type];
    if (subKey && subscriptions[subKey]) {
      subscriptions[subKey].forEach((handler) => handler(event as any));
    }
  });
}

export const on = {
  delta: (cb: EventCallback<ChatDeltaEvent>) => {
    subscriptions.delta.add(cb);
    return () => subscriptions.delta.delete(cb);
  },
  reasoning: (cb: EventCallback<ChatReasoningEvent>) => {
    subscriptions.reasoning.add(cb);
    return () => subscriptions.reasoning.delete(cb);
  },
  toolCall: (cb: EventCallback<ChatToolCallEvent>) => {
    subscriptions.toolCall.add(cb);
    return () => subscriptions.toolCall.delete(cb);
  },
  toolResult: (cb: EventCallback<ChatToolResultEvent>) => {
    subscriptions.toolResult.add(cb);
    return () => subscriptions.toolResult.delete(cb);
  },
  complete: (cb: EventCallback<ChatCompleteEvent>) => {
    subscriptions.complete.add(cb);
    return () => subscriptions.complete.delete(cb);
  },
  error: (cb: EventCallback<ChatErrorEvent>) => {
    subscriptions.errorEvents.add(cb);
    return () => subscriptions.errorEvents.delete(cb);
  },
  sessionChanged: (cb: EventCallback<SessionChangedEvent>) => {
    subscriptions.sessionChanged.add(cb);
    return () => subscriptions.sessionChanged.delete(cb);
  },
  toolProgress: (cb: EventCallback<ToolProgressEvent>) => {
    subscriptions.toolProgress.add(cb);
    return () => subscriptions.toolProgress.delete(cb);
  },
  approvalRequest: (cb: EventCallback<ApprovalRequestEvent>) => {
    subscriptions.approvalRequest.add(cb);
    return () => subscriptions.approvalRequest.delete(cb);
  },
};
