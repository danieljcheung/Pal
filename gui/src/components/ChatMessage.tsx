import { useEffect, useState } from "react";
import "./ChatMessage.css";

interface ChatMessageProps {
  text: string;
  isThinking?: boolean;
}

function ChatMessage({ text, isThinking = false }: ChatMessageProps) {
  const [visible, setVisible] = useState(false);

  // Trigger fade-in animation on mount or text change
  useEffect(() => {
    setVisible(false);
    const timer = requestAnimationFrame(() => {
      requestAnimationFrame(() => setVisible(true));
    });
    return () => cancelAnimationFrame(timer);
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
    <div className={`chat-message ${visible ? "chat-message--visible" : ""}`}>
      {text}
    </div>
  );
}

export default ChatMessage;
