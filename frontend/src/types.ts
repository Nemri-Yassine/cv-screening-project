export type Mode = "agent" | "rag";

export interface Source {
  file_name: string;
  category: string;
  job_title: string;
  years_experience: number;
  education_level: string;
  skills: string[];
  summary: string;
  profile: string;
  cited?: boolean;
  citation_index?: number | null;
}

export interface ToolCall {
  name: string;
  args: Record<string, unknown>;
}

export interface SearchFilters {
  search_query: string;
  category: string;
  min_years: number;
}

export interface ChatResponse {
  answer: string;
  sources: Source[];
  tool_calls: ToolCall[];
  filters: SearchFilters | null;
  mode: Mode;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  toolCalls?: ToolCall[];
  filters?: SearchFilters | null;
  mode?: Mode;
  error?: boolean;
}

export interface Health {
  status: string;
  cv_count: number;
}
