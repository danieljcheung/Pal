/**
 * API client for communicating with Pal's Python backend.
 */

const API_BASE = "http://127.0.0.1:8000";

export type Mood =
  | "happy"
  | "curious"
  | "excited"
  | "thinking"
  | "confused"
  | "sad"
  | "worried"
  | "sleepy";

export interface Identity {
  name: string;
  owner_name: string | null;
  mood: Mood;
  born: string | null;
  age: string;
  first_boot: boolean;
}

export interface ChatResponse {
  response: string;
  mood: Mood;
  skill_unlocked: string | null;
}

export interface Stats {
  messages_exchanged: number;
  memories_stored: number;
  emotional_shares: number;
  questions_asked: number;
  questions_answered: number;
  corrections: number;
  reminders_requested: number;
  reminders_delivered: number;
  thought_dumps: number;
  check_ins: number;
  tasks_given: number;
  tasks_completed: number;
  first_met: string | null;
  last_interaction: string | null;
  unique_days: string[];
}

export interface Skill {
  unlocked: boolean;
  level: number;
  uses: number;
}

export interface InnerLife {
  thought_queue: Array<{
    thought: string;
    type: string;
    formed_at: string;
    surfaced: boolean;
  }>;
  dream_journal: Array<{
    dream: string;
    formed_at: string;
    shared: boolean;
  }>;
  last_dream_time: string | null;
  dreams_since_last_conversation: number;
}

export interface Topic {
  display_name: string;
  first_mentioned: string;
  last_discussed: string;
  times_discussed: number;
  memories: string[];
  understanding: "surface" | "basic" | "familiar" | "knowledgeable";
  unresolved: string[];
}

export interface Brain {
  stats: Stats;
  skills: Record<string, Skill>;
  topics: Record<string, Topic>;
  inner_life: InnerLife;
  memory_count: number;
  memories: Memory[];
}

export interface Memory {
  id: string;
  content: string;
  type: string;
  source: string;
  timestamp: string;
}

/**
 * Fetch Pal's current identity state.
 */
export async function fetchIdentity(): Promise<Identity> {
  const response = await fetch(`${API_BASE}/identity`);
  if (!response.ok) {
    throw new Error(`Failed to fetch identity: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Send a message to Pal and get a response.
 */
export async function sendMessage(message: string): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ message }),
  });

  if (!response.ok) {
    throw new Error(`Failed to send message: ${response.statusText}`);
  }

  return response.json();
}

export interface StreamChunk {
  type: "chunk";
  text: string;
}

export interface StreamDone {
  type: "done";
  mood: Mood;
  skill_unlocked: string | null;
}

export type StreamEvent = StreamChunk | StreamDone;

/**
 * Send a message to Pal and get a streaming response.
 * Calls onChunk for each text chunk, and onDone when complete.
 */
export async function sendMessageStream(
  message: string,
  onChunk: (text: string) => void,
  onDone: (mood: Mood, skillUnlocked: string | null) => void
): Promise<void> {
  const response = await fetch(`${API_BASE}/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ message }),
  });

  if (!response.ok) {
    throw new Error(`Failed to send message: ${response.statusText}`);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error("No response body");
  }

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // Process complete SSE messages
    const lines = buffer.split("\n");
    buffer = lines.pop() || ""; // Keep incomplete line in buffer

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        const data = line.slice(6);
        try {
          const event: StreamEvent = JSON.parse(data);
          if (event.type === "chunk") {
            onChunk(event.text);
          } else if (event.type === "done") {
            onDone(event.mood, event.skill_unlocked);
          }
        } catch {
          // Ignore parse errors
        }
      }
    }
  }
}

/**
 * Fetch Pal's brain data for visualization.
 */
export async function fetchBrain(): Promise<Brain> {
  const response = await fetch(`${API_BASE}/brain`);
  if (!response.ok) {
    throw new Error(`Failed to fetch brain: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Fetch conversation history (memories).
 */
export async function fetchHistory(): Promise<{ memories: Memory[] }> {
  const response = await fetch(`${API_BASE}/history`);
  if (!response.ok) {
    throw new Error(`Failed to fetch history: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Reset the conversation session.
 */
export async function resetSession(): Promise<void> {
  const response = await fetch(`${API_BASE}/reset-session`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error(`Failed to reset session: ${response.statusText}`);
  }
}

/**
 * Check if the backend is running.
 */
export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/`);
    return response.ok;
  } catch {
    return false;
  }
}
