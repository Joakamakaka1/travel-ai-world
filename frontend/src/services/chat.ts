/**
 * AI chat against ai_api (Server-Sent Events).
 */

import type { components } from "@/types/generated/ai-api";
import { apiUrl, authHeaders, readErrorMessage, UnauthorizedError } from "./http";

export type ChatMessage = components["schemas"]["ChatMessage"];
type ChatRequest = components["schemas"]["ChatRequest"];

/**
 * Streams a chat completion. Yields content chunks as they arrive.
 *
 * Wire format, one JSON object per `data:` line, terminated by `[DONE]`:
 *   data: {"content": "Hola"}
 *   data: {"error": "..."}
 *   data: [DONE]
 */
export async function* streamChat(
  message: string,
  history: ChatMessage[]
): AsyncGenerator<string, void, unknown> {
  const body: ChatRequest = { message, history };
  const res = await fetch(apiUrl("ai", "/ai/chat"), {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(body),
  });

  if (res.status === 401) {
    throw new UnauthorizedError("Session expired or invalid");
  }
  if (!res.ok) {
    throw new Error(await readErrorMessage(res, "Chat service unavailable"));
  }

  const reader = res.body?.getReader();
  if (!reader) throw new Error("No response body");

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const data = line.slice(6).trim();
      if (data === "[DONE]") return;
      try {
        const parsed = JSON.parse(data) as { content?: string; error?: string };
        if (parsed.error) throw new Error(parsed.error);
        if (parsed.content) yield parsed.content;
      } catch (err) {
        if (err instanceof SyntaxError) continue; // malformed chunk: skip
        throw err;
      }
    }
  }
}
