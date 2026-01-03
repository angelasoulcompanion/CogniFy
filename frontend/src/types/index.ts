/**
 * CogniFy Frontend Types
 * Created with love by Angela & David - 1 January 2026
 */

// =============================================================================
// AUTH TYPES
// =============================================================================

export interface User {
  user_id: string;
  email: string;
  full_name: string | null;
  role: 'admin' | 'editor' | 'user';
  is_active: boolean;
  created_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  setUser: (user: User) => void;
}

// =============================================================================
// DOCUMENT TYPES
// =============================================================================

export type ProcessingStep = 'pending' | 'extracting' | 'chunking' | 'embedding' | 'storing' | 'completed';

export interface Document {
  document_id: string;
  filename: string;
  original_filename: string;
  file_type: string;
  file_size_bytes: number;
  title: string | null;
  description: string | null;
  page_count: number | null;
  language: string;
  tags: string[];
  processing_status: 'pending' | 'processing' | 'completed' | 'failed';
  processing_step: ProcessingStep | null;
  processing_progress: number | null;
  processing_error: string | null;
  total_chunks: number;
  created_at: string;
  processed_at: string | null;
}

export interface DocumentChunk {
  chunk_id: string;
  document_id: string;
  chunk_index: number;
  content: string;
  page_number: number | null;
  section_title: string | null;
  token_count: number;
}

export interface DocumentUploadResponse {
  document: Document;
  message: string;
}

export interface DocumentStats {
  total_chunks: number;
  with_embeddings: number;
  without_embeddings: number;
  completion_rate: number;
}

// =============================================================================
// SEARCH TYPES
// =============================================================================

export interface SearchRequest {
  query: string;
  limit?: number;
  threshold?: number;
  similarity_method?: 'cosine' | 'euclidean' | 'dot';
  document_ids?: string[];
  include_content?: boolean;
}

export interface SearchResult {
  chunk_id: string;
  document_id: string;
  document_name: string;
  content: string;
  page_number: number | null;
  section_title: string | null;
  similarity: number;
  highlight?: string;
  vector_rank?: number;
  bm25_rank?: number;
  rrf_score?: number;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  total: number;
  search_time_ms: number;
  search_method: string;
}

// =============================================================================
// CHAT TYPES
// =============================================================================

export interface RAGSettings {
  similarity_threshold: number;
  max_chunks: number;
  similarity_method: 'cosine' | 'euclidean' | 'dot';
  search_method: 'vector' | 'bm25' | 'hybrid';
  bm25_weight: number;
  vector_weight: number;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  rag_enabled?: boolean;
  rag_settings?: RAGSettings;
  document_ids?: string[];
  provider?: 'ollama' | 'openai';
  model?: string;
  stream?: boolean;
}

export interface SourceReference {
  index: number;
  document_id: string;
  document_name: string;
  page_number: number | null;
  section: string | null;
  content_preview: string;
  score: number;
}

export interface ChatMessage {
  message_id: string;
  conversation_id: string;
  message_type: 'user' | 'assistant' | 'system';
  content: string;
  sources: SourceReference[] | null;
  response_time_ms: number | null;
  created_at: string;
  isStreaming?: boolean;
}

export interface Conversation {
  conversation_id: string;
  user_id: string | null;
  title: string | null;
  model_provider: string;
  model_name: string;
  rag_enabled: boolean;
  message_count: number;
  created_at: string;
  updated_at: string;
}

// =============================================================================
// SSE EVENT TYPES
// =============================================================================

export interface SSESessionEvent {
  type: 'session';
  conversation_id: string;
  model: string;
  provider: string;
}

export interface SSESearchStartEvent {
  type: 'search_start';
  query: string;
}

export interface SSESearchResultsEvent {
  type: 'search_results';
  count: number;
  sources: Array<{
    document: string;
    page: number | null;
    score: number;
  }>;
}

export interface SSEContentEvent {
  type: 'content';
  content: string;
}

export interface SSEContentCompleteEvent {
  type: 'content_complete';
  content: string;
}

// Structured Response Types
export interface StructuredContentItem {
  type: 'text' | 'fact' | 'list_item';
  text?: string;
  label?: string;
  value?: string;
}

export interface StructuredSection {
  heading: string;
  items: StructuredContentItem[];
}

export interface StructuredResponse {
  title: string;
  sections: StructuredSection[];
  sources_used: number[];
  raw_text?: string;
}

export interface SSEStructuredResponseEvent {
  type: 'structured_response';
  structured: StructuredResponse;
}

export interface SSESourcesEvent {
  type: 'sources';
  sources: SourceReference[];
}

export interface SSEDoneEvent {
  type: 'done';
  message_id: string;
  response_time_ms: number;
  final_content?: string;  // Post-processed content from backend
}

export interface SSEErrorEvent {
  type: 'error';
  error: string;
}

export type SSEEvent =
  | SSESessionEvent
  | SSESearchStartEvent
  | SSESearchResultsEvent
  | SSEContentEvent
  | SSEContentCompleteEvent
  | SSEStructuredResponseEvent
  | SSESourcesEvent
  | SSEDoneEvent
  | SSEErrorEvent;

// =============================================================================
// UI STATE TYPES
// =============================================================================

export interface ChatState {
  conversations: Conversation[];
  currentConversation: Conversation | null;
  messages: ChatMessage[];
  isStreaming: boolean;
  streamingContent: string;
  sources: SourceReference[];
}

export interface AppState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  ragSettings: RAGSettings;
}

// =============================================================================
// DATABASE CONNECTOR TYPES
// =============================================================================

export type DatabaseType = 'postgresql' | 'mysql' | 'sqlserver';
export type SyncStatus = 'pending' | 'syncing' | 'completed' | 'failed';

export interface DatabaseConnection {
  connection_id: string;
  name: string;
  db_type: DatabaseType;
  host: string;
  port: number;
  database_name: string;
  username: string;
  sync_enabled: boolean;
  last_sync_at: string | null;
  last_sync_status: SyncStatus | null;
  last_sync_error: string | null;
  total_chunks_synced: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TableColumn {
  column_name: string;
  data_type: string;
  is_nullable: string;
  column_default: string | null;
  character_maximum_length: number | null;
}

export interface TableInfo {
  table_name: string;
  schema_name: string;
  column_count: number;
  row_count: number | null;
  columns: TableColumn[];
  primary_key: string | null;
  description: string | null;
}

export interface ConnectionCreateRequest {
  name: string;
  db_type: DatabaseType;
  host: string;
  port: number;
  database_name: string;
  username: string;
  password: string;
}

export interface ConnectionTestResponse {
  success: boolean;
  error: string | null;
}

export interface SyncResponse {
  success: boolean;
  chunks_created: number;
  error: string | null;
}

// =============================================================================
// ADMIN TYPES
// =============================================================================

export interface SystemStats {
  total_users: number;
  active_users_7d: number;
  total_documents: number;
  total_chunks: number;
  total_conversations: number;
  total_messages: number;
  total_embeddings: number;
  storage_used_mb: number;
  avg_response_time_ms: number;
}

export interface UserStats {
  user_id: string;
  email: string;
  full_name: string | null;
  role: string;
  is_active: boolean;
  document_count: number;
  conversation_count: number;
  message_count: number;
  last_active: string | null;
  created_at: string;
}

export interface UserListResponse {
  users: UserStats[];
  total: number;
  skip: number;
  limit: number;
}

export interface UsageMetrics {
  date: string;
  documents_uploaded: number;
  messages_sent: number;
  embeddings_created: number;
  unique_users: number;
}

export interface DocumentTypeStats {
  file_type: string;
  count: number;
  total_size_mb: number;
  total_chunks: number;
}

export interface TopUser {
  user_id: string;
  email: string;
  full_name: string | null;
  conversations: number;
  messages: number;
  documents: number;
}

export interface ActivityItem {
  type: 'document' | 'conversation';
  id: string;
  title: string;
  user_email: string;
  timestamp: string;
}
