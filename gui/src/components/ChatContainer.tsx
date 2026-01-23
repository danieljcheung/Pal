import { useState, useCallback, useEffect, useRef } from "react";
import Face from "./Face";
import ChatMessage from "./ChatMessage";
import ChatInput, { type ChatInputHandle } from "./ChatInput";
import {
  fetchIdentity,
  sendMessageStream,
  detectResearchIntent,
  researchUrl,
  researchSearch,
  researchText,
  type Mood,
  type ResearchResponse,
} from "../api";
import { useSettings } from "../contexts/SettingsContext";
import { playChime, resumeAudio } from "../utils/sound";
import { sendNotification } from "../utils/notifications";
import "./ChatContainer.css";

type WindowMode = "full" | "widget" | "floating";

// Strip mood tags from text (safety net for client-side)
function stripMoodTag(text: string): string {
  return text.replace(/\s*\[mood:\w+\]\s*/g, "").trim();
}

// Idle timeout in milliseconds (2.5 minutes)
const IDLE_TIMEOUT = 150000;

// Messages Pal says when dropping a thought
const IDLE_MESSAGES = [
  "...nevermind",
  "...",
  "hmm...",
];

// Messages Pal says when starting research
const RESEARCH_MESSAGES = {
  url: ["Let me read that...", "Looking at that link...", "I'll check it out..."],
  search: ["Let me search for that...", "I'll look that up...", "Searching..."],
  text: ["That's a lot. Let me read it...", "Let me process that...", "Reading..."],
};

// Format research response into a message
function formatResearchResponse(result: ResearchResponse): string {
  if (!result.success) {
    return result.error || "I couldn't do that research.";
  }

  let response = result.summary;

  // Add facts stored
  if (result.facts_stored > 0) {
    response += ` I remembered ${result.facts_stored} thing${result.facts_stored > 1 ? "s" : ""} about ${result.topic}.`;
  }

  // Add questions
  if (result.questions && result.questions.length > 0) {
    const question = result.questions[0];
    response += ` I'm still wondering though - ${question}`;
  }

  return response;
}

interface Message {
  id: string;
  text: string;
  from: "pal" | "user";
}

interface ChatContainerProps {
  initialMessage?: string;
  mode?: WindowMode;
}

function ChatContainer({
  initialMessage = "",
  mode = "full",
}: ChatContainerProps) {
  const [currentMessage, setCurrentMessage] = useState<Message | null>(
    initialMessage ? { id: "initial", text: initialMessage, from: "pal" } : null
  );
  const [mood, setMood] = useState<Mood>("curious");
  const [isThinking, setIsThinking] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isResearching, setIsResearching] = useState(false);
  const [backendConnected, setBackendConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const streamingTextRef = useRef("");
  const inputRef = useRef<ChatInputHandle>(null);
  const idleTimeoutRef = useRef<number | null>(null);
  const lastResponseTimeRef = useRef<number>(Date.now());
  const { settings } = useSettings();

  // Play chime when Pal finishes speaking (if sounds enabled)
  const playResponseSound = useCallback(() => {
    if (settings.sounds_enabled) {
      playChime();
    }
  }, [settings.sounds_enabled]);

  // Resume audio context on first user interaction
  useEffect(() => {
    const handleInteraction = () => {
      resumeAudio();
      document.removeEventListener("click", handleInteraction);
      document.removeEventListener("keydown", handleInteraction);
    };

    document.addEventListener("click", handleInteraction);
    document.addEventListener("keydown", handleInteraction);

    return () => {
      document.removeEventListener("click", handleInteraction);
      document.removeEventListener("keydown", handleInteraction);
    };
  }, []);

  // Reset idle timeout
  const resetIdleTimeout = useCallback(() => {
    if (idleTimeoutRef.current) {
      clearTimeout(idleTimeoutRef.current);
    }

    lastResponseTimeRef.current = Date.now();

    // Only set timeout if there's a message waiting for response
    if (currentMessage && currentMessage.from === "pal" && !isThinking && !isStreaming) {
      idleTimeoutRef.current = window.setTimeout(async () => {
        // Pick a random idle message
        const idleMsg = IDLE_MESSAGES[Math.floor(Math.random() * IDLE_MESSAGES.length)];
        setCurrentMessage({
          id: "idle",
          text: idleMsg,
          from: "pal",
        });
        setMood("sleepy");

        // Send notification if enabled (for idle thoughts)
        if (settings.notifications_enabled && idleMsg !== "...") {
          try {
            await sendNotification(settings.pal_name || "Pal", idleMsg);
          } catch {
            // Ignore notification errors
          }
        }

        // After a moment, clear the message
        setTimeout(() => {
          setCurrentMessage(null);
          setMood("curious");
        }, 2000);
      }, IDLE_TIMEOUT);
    }
  }, [currentMessage, isThinking, isStreaming, settings.notifications_enabled, settings.pal_name]);

  // Start idle timer when Pal finishes speaking
  useEffect(() => {
    if (!isThinking && !isStreaming && currentMessage?.from === "pal") {
      resetIdleTimeout();
    }

    return () => {
      if (idleTimeoutRef.current) {
        clearTimeout(idleTimeoutRef.current);
      }
    };
  }, [isThinking, isStreaming, currentMessage, resetIdleTimeout]);

  // Fetch identity on mount to get current mood
  useEffect(() => {
    const loadIdentity = async () => {
      try {
        const identity = await fetchIdentity();
        setMood(identity.mood);
        setBackendConnected(true);
        setError(null);

        // Set greeting message if no initial message provided
        if (!initialMessage && mode === "full") {
          const greeting = identity.owner_name
            ? `Hi ${identity.owner_name}!`
            : "Hi! I'm Pal.";
          setCurrentMessage({
            id: "greeting",
            text: greeting,
            from: "pal",
          });
        }
      } catch {
        setBackendConnected(false);
        setError("Backend not connected. Start the server with: python server.py");
        // Set fallback message
        if (!initialMessage && mode === "full") {
          setCurrentMessage({
            id: "error",
            text: "Waiting for backend...",
            from: "pal",
          });
        }
      }
    };

    loadIdentity();
  }, [initialMessage, mode]);

  const handleSend = useCallback(async (text: string) => {
    if (!backendConnected) {
      setError("Backend not connected");
      return;
    }

    // Clear idle timeout when user sends message
    if (idleTimeoutRef.current) {
      clearTimeout(idleTimeoutRef.current);
    }

    const messageId = Date.now().toString();

    // Check for research intent
    const researchIntent = detectResearchIntent(text);

    if (researchIntent) {
      // Research request - handle differently
      setIsResearching(true);
      setIsThinking(true);
      setIsStreaming(false);
      setMood("thinking");
      setError(null);

      // Show initial research message
      const messages = RESEARCH_MESSAGES[researchIntent.type];
      const initialMsg = messages[Math.floor(Math.random() * messages.length)];
      setCurrentMessage({
        id: messageId,
        text: initialMsg,
        from: "pal",
      });

      try {
        let result: ResearchResponse;

        // Call appropriate research endpoint
        switch (researchIntent.type) {
          case "url":
            result = await researchUrl(researchIntent.content);
            break;
          case "search":
            result = await researchSearch(researchIntent.content);
            break;
          case "text":
            result = await researchText(researchIntent.content);
            break;
        }

        // Format and display response
        const responseText = formatResearchResponse(result);
        setCurrentMessage({
          id: messageId,
          text: responseText,
          from: "pal",
        });

        // Set mood based on success
        if (result.skill_locked) {
          setMood("confused");
        } else if (result.success) {
          setMood("happy");
        } else {
          setMood("confused");
        }

        // Brief bounce effect and sound
        setIsSpeaking(true);
        setTimeout(() => setIsSpeaking(false), 250);
        playResponseSound();

      } catch (err) {
        setMood("confused");
        setError("Research failed");
        setCurrentMessage({
          id: messageId,
          text: "...something went wrong while I was reading that.",
          from: "pal",
        });
      } finally {
        setIsResearching(false);
        setIsThinking(false);
      }

      return;
    }

    // Normal chat flow
    setIsThinking(true);
    setIsStreaming(false);
    setMood("thinking");
    setCurrentMessage(null);
    setError(null);
    streamingTextRef.current = "";

    try {
      await sendMessageStream(
        text,
        // onChunk - called for each text chunk
        (chunk) => {
          // First chunk: switch from thinking to streaming
          if (!streamingTextRef.current) {
            setIsThinking(false);
            setIsStreaming(true);
            setIsSpeaking(true);
          }

          streamingTextRef.current += chunk;
          // Strip any mood tags that slip through (safety net)
          const cleanText = stripMoodTag(streamingTextRef.current);
          setCurrentMessage({
            id: messageId,
            text: cleanText,
            from: "pal",
          });
        },
        // onDone - called when streaming completes
        (finalMood, skillUnlocked) => {
          setIsStreaming(false);
          setMood(finalMood);

          // Brief bounce effect at completion and sound
          setIsSpeaking(true);
          setTimeout(() => setIsSpeaking(false), 250);
          playResponseSound();

          // Log skill unlock if any
          if (skillUnlocked) {
            console.log(`Skill unlocked: ${skillUnlocked}`);
          }
        }
      );
    } catch (err) {
      setIsThinking(false);
      setIsStreaming(false);
      setMood("confused");
      setError("Failed to get response");
      setCurrentMessage({
        id: messageId,
        text: "...I couldn't hear that. Something went wrong.",
        from: "pal",
      });
    }
  }, [backendConnected]);

  // Click anywhere to focus input (full mode only)
  const handleContainerClick = useCallback((e: React.MouseEvent) => {
    // Don't focus if clicking on controls or if already focused on input
    const target = e.target as HTMLElement;
    if (
      target.closest(".app-header") ||
      target.closest(".chat-input") ||
      target.tagName === "BUTTON" ||
      target.tagName === "INPUT"
    ) {
      return;
    }

    // Focus the input
    inputRef.current?.focus();
  }, []);

  // Floating mode: just the face
  if (mode === "floating") {
    return (
      <div className="chat-container chat-container--floating">
        <div className="chat-container__face chat-container__face--floating">
          <Face mood={mood} isThinking={isThinking} isSpeaking={isSpeaking} />
        </div>
      </div>
    );
  }

  // Widget mode: face + message only
  if (mode === "widget") {
    return (
      <div className="chat-container chat-container--widget">
        <div className="chat-container__face chat-container__face--widget">
          <Face mood={mood} isThinking={isThinking} isSpeaking={isSpeaking} />
        </div>
        <div className="chat-container__message chat-container__message--widget">
          <ChatMessage
            text={currentMessage?.text || ""}
            isThinking={isThinking}
          />
        </div>
      </div>
    );
  }

  // Full mode: everything
  return (
    <div className="chat-container" onClick={handleContainerClick}>
      <div className="chat-container__main">
        <div className="chat-container__face">
          <Face mood={mood} isThinking={isThinking} isSpeaking={isSpeaking} />
        </div>

        <div className="chat-container__message">
          <ChatMessage
            text={currentMessage?.text || ""}
            isThinking={isThinking}
            isStreaming={isStreaming}
          />
        </div>

        {error && (
          <div className="chat-container__error">
            {error}
          </div>
        )}
      </div>

      <div className="chat-container__input">
        <ChatInput
          ref={inputRef}
          onSend={handleSend}
          disabled={isThinking || isStreaming || isResearching || !backendConnected}
        />
      </div>
    </div>
  );
}

export default ChatContainer;
