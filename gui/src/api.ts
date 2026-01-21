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

export interface Brain {
  stats: Stats;
  skills: Record<string, Skill>;
  topics: Record<string, unknown>;
  inner_life: InnerLife;
  memory_count: number;
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
