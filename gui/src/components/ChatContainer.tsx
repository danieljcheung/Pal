import { useState, useCallback, useEffect, useRef } from "react";
import Face from "./Face";
import ChatMessage from "./ChatMessage";
import ChatInput from "./ChatInput";
import { fetchIdentity, sendMessageStream, type Mood } from "../api";
import "./ChatContainer.css";

type WindowMode = "full" | "widget" | "floating";

// Strip mood tags from text (safety net for client-side)
function stripMoodTag(text: string): string {
  return text.replace(/\s*\[mood:\w+\]\s*/g, "").trim();
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
  const [backendConnected, setBackendConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const streamingTextRef = useRef("");

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

    // Start thinking immediately
    setIsThinking(true);
    setIsStreaming(false);
    setMood("thinking");
    setCurrentMessage(null);
    setError(null);
    streamingTextRef.current = "";

    const messageId = Date.now().toString();

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

          // Brief bounce effect at completion
          setIsSpeaking(true);
          setTimeout(() => setIsSpeaking(false), 250);

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
    <div className="chat-container">
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
        <ChatInput onSend={handleSend} disabled={isThinking || isStreaming || !backendConnected} />
      </div>
    </div>
  );
}

export default ChatContainer;
