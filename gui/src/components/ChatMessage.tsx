import { useEffect, useState, useRef } from "react";
import "./ChatMessage.css";

interface ChatMessageProps {
  text: string;
  isThinking?: boolean;
  isStreaming?: boolean;
}

function ChatMessage({ text, isThinking = false, isStreaming = false }: ChatMessageProps) {
  const [visible, setVisible] = useState(false);
  const prevTextRef = useRef("");

  // Trigger fade-in animation on mount or when text first appears
  useEffect(() => {
    // Only animate on initial appearance, not during streaming
    if (!isStreaming && text && !prevTextRef.current) {
      setVisible(false);
      const timer = requestAnimationFrame(() => {
        requestAnimationFrame(() => setVisible(true));
      });
      return () => cancelAnimationFrame(timer);
    } else if (text) {
      setVisible(true);
    }
    prevTextRef.current = text;
  }, [text, isStreaming]);

  // Reset when text clears
  useEffect(() => {
    if (!text) {
      setVisible(false);
      prevTextRef.current = "";
    }
  }, [text]);

  if (isThinking) {
    return (
      <div className="chat-message chat-message--thinking">
        <span className="thinking-dots">
          <span>.</span>
          <span>.</span>
          <span>.</span>
        </span>
      </div>
    );
  }

  if (!text) return null;

  return (
    <div className={`chat-message ${visible ? "chat-message--visible" : ""} ${isStreaming ? "chat-message--streaming" : ""}`}>
      {text}
      {isStreaming && <span className="streaming-cursor">|</span>}
    </div>
  );
}

export default ChatMessage;
