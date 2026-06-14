/**
 * CIEL TUI - Gateway Protocol Types
 * JSON-RPC 2.0 over stdio
 */

// Base JSON-RPC 2.0
export interface JSONRPCRequest {
  jsonrpc: '2.0';
  id: string | number;
  method: string;
  params?: Record<string, unknown>;
}

export interface JSONRPCResponse {
  jsonrpc: '2.0';
  id: string | number;
  result?: unknown;
  error?: JSONRPCError;
}

export interface JSONRPCNotification {
  jsonrpc: '2.0';
  method: string;
  params?: Record<string, unknown>;
}

export interface JSONRPCError {
  code: number;
  message: string;
  data?: unknown;
}

export type JSONRPCMessage = JSONRPCRequest | JSONRPCResponse | JSONRPCNotification;

// Gateway Methods
export type GatewayMethod =
  | 'chat.stream'
  | 'tools.execute'
  | 'tools.list'
  | 'sessions.create'
  | 'sessions.list'
  | 'sessions.get'
  | 'sessions.delete'
  | 'approvals.respond'
  | 'config.get'
  | 'config.set'
  | 'completions.slash'
  | 'completions.path';

// Chat Types
export interface ChatStreamParams {
  messages: ChatMessage[];
  provider?: string;
  model?: string;
  temperature?: number;
  maxTokens?: number;
  sessionId?: string;
}

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant' | 'tool';
  content: string;
  reasoning?: string;
  toolCalls?: ToolCall[];
  toolCallId?: string;
  name?: string;
}

export interface ToolCall {
  id: string;
  type: 'function';
  function: {
    name: string;
    arguments: string;
  };
}

// Chat Stream Events
export interface ChatDeltaEvent {
  type: 'delta';
  token: string;
  reasoning?: string;
}

export interface ChatReasoningEvent {
  type: 'reasoning';
  content: string;
}

export interface ChatToolCallEvent {
  type: 'tool_call';
  toolCall: ToolCall;
}

export interface ChatToolResultEvent {
  type: 'tool_result';
  toolCallId: string;
  result: string;
  error?: string;
}

export interface ChatCompleteEvent {
  type: 'complete';
  message: ChatMessage;
  usage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
  sessionId: string;
}

export interface ChatErrorEvent {
  type: 'error';
  code: string;
  message: string;
}

export type ChatStreamEvent =
  | ChatDeltaEvent
  | ChatReasoningEvent
  | ChatToolCallEvent
  | ChatToolResultEvent
  | ChatCompleteEvent
  | ChatErrorEvent;

// Tools
export interface ToolExecuteParams {
  name: string;
  arguments: Record<string, unknown>;
  sessionId?: string;
  taskId?: string;
}

export interface ToolExecuteResult {
  success: boolean;
  result?: string;
  error?: string;
  duration?: number;
}

export interface ToolDefinition {
  name: string;
  description: string;
  parameters: {
    type: 'object';
    properties: Record<string, unknown>;
    required?: string[];
  };
  toolset: string;
  requiresApproval?: boolean;
}

// Sessions
export interface SessionCreateParams {
  source: string;
  platform: string;
  cwd?: string;
  parentSessionId?: string;
}

export interface SessionInfo {
  id: string;
  source: string;
  platform: string;
  cwd?: string;
  createdAt: number;
  updatedAt: number;
  parentSessionId?: string;
  messageCount: number;
  model?: string;
  provider?: string;
}

export interface SessionListParams {
  limit?: number;
  offset?: number;
  source?: string;
  platform?: string;
}

export interface SessionListResult {
  sessions: SessionInfo[];
  total: number;
}

export interface SessionGetParams {
  id: string;
}

export interface SessionDeleteParams {
  id: string;
}

// Approvals
export interface ApprovalRequestEvent {
  type: 'approval_request';
  id: string;
  tool: string;
  arguments: Record<string, unknown>;
  message: string;
  options: string[];
  defaultOption: string;
  timeout: number;
}

export interface ApprovalRespondParams {
  id: string;
  response: string;
}

export interface ApprovalRespondResult {
  success: boolean;
}

// Config
export interface ConfigGetParams {
  key: string;
}

export interface ConfigGetResult {
  value: unknown;
}

export interface ConfigSetParams {
  key: string;
  value: unknown;
}

export interface ConfigSetResult {
  success: boolean;
}

// Completions
export interface SlashCompletionParams {
  query: string;
  context?: string;
}

export interface SlashCompletionResult {
  completions: string[];
}

export interface PathCompletionParams {
  query: string;
  cwd?: string;
}

export interface PathCompletionResult {
  completions: string[];
}

// Gateway Status
export interface GatewayReadyEvent {
  type: 'gateway.ready';
  version: string;
  skin: SkinConfig;
  capabilities: string[];
}

export interface SessionChangedEvent {
  type: 'session.changed';
  session: SessionInfo | null;
}

export interface ToolProgressEvent {
  type: 'tool.progress';
  tool: string;
  progress: number;
  message?: string;
}

export type GatewayEvent =
  | GatewayReadyEvent
  | SessionChangedEvent
  | ToolProgressEvent
  | ChatStreamEvent
  | ApprovalRequestEvent;

// Skin Config
export interface SkinColors {
  bannerBorder: string;
  bannerTitle: string;
  bannerAccent: string;
  bannerDim: string;
  bannerText: string;
  responseBorder: string;
  toolOutput: string;
  error: string;
  warning: string;
  success: string;
  muted: string;
}

export interface SkinSpinner {
  waitingFaces: string[];
  thinkingFaces: string[];
  thinkingVerbs: string[];
  wings?: string[][];
}

export interface SkinBranding {
  agentName: string;
  welcome: string;
  responseLabel: string;
  promptSymbol: string;
}

export interface SkinConfig {
  name: string;
  description: string;
  colors: SkinColors;
  spinner: SkinSpinner;
  branding: SkinBranding;
  toolPrefix: string;
  toolEmojis: Record<string, string>;
}

// Session State (for nanostores)
export interface SessionState {
  currentSession: SessionInfo | null;
  sessions: SessionInfo[];
  loading: boolean;
  error: string | null;
}

// Chat State (for nanostores)
export interface ChatState {
  messages: ChatMessage[];
  streaming: boolean;
  currentToken: string;
  reasoning: string;
  pendingToolCalls: ToolCall[];
  pendingApprovals: ApprovalRequestEvent[];
}

// UI State (for nanostores)
export interface UIState {
  skin: SkinConfig;
  sidebarOpen: boolean;
  activityFeedOpen: boolean;
  statusBarVisible: boolean;
  commandPaletteOpen: boolean;
}

// Gateway Connection State
export interface GatewayConnectionState {
  connected: boolean;
  connecting: boolean;
  error: string | null;
  capabilities: string[];
  skin: SkinConfig | null;
}