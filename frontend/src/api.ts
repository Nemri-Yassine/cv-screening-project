import type { ChatResponse, Health, Message, Mode, Source } from "./types";

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init);
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `${response.status} ${response.statusText}`);
  }
  return response.json();
}

export function getHealth() {
  return request<Health>("/api/health");
}

export function getCandidate(fileName: string) {
  return request<Source>(`/api/candidates/${encodeURIComponent(fileName)}`);
}

export function cvUrl(fileName: string) {
  return `/api/cvs/${encodeURIComponent(fileName)}`;
}

export function sendChat(question: string, mode: Mode, previous: Message[]) {
  const history = previous
    .filter((message) => !message.error)
    .map(({ role, content }) => ({ role, content }));

  return request<ChatResponse>("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, mode, history }),
  });
}
