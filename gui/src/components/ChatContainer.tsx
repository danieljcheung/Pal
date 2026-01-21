import { useState, useCallback } from "react";
import Face from "./Face";
import ChatMessage from "./ChatMessage";
import ChatInput from "./ChatInput";
import "./ChatContainer.css";

type Mood = "happy" | "curious" | "excited" | "thinking" | "confused" | "sad" | "worried" | "sleepy";

interface Message {
  id: string;
  text: string;
  from: "pal" | "user";
}

interface ChatContainerProps {
  initialMessage?: string;
}

function ChatContainer({ initialMessage = "Hi! How can I help you today?" }: ChatContainerProps) {
  const [currentMessage, setCurrentMessage] = useState<Message | null>({
    id: "initial",
    text: initialMessage,
    from: "pal",
  });
  const [mood, setMood] = useState<Mood>("curious");
  const [isThinking, setIsThinking] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);

  const handleSend = useCallback((text: string) => {
    // Start thinking
    setIsThinking(true);
    setMood("thinking");
    setCurrentMessage(null);

    // Simulate response (placeholder - no backend yet)
    setTimeout(() => {
      setIsThinking(false);

      // Determine mood based on message content (simple placeholder logic)
      let responseMood: Mood = "happy";
      let response = "";

      const lowerText = text.toLowerCase();
      if (lowerText.includes("help") || lowerText.includes("?")) {
        responseMood = "curious";
        response = "I'd be happy to help! What would you like to know?";
      } else if (lowerText.includes("thank")) {
        responseMood = "happy";
        response = "You're welcome!";
      } else if (lowerText.includes("hello") || lowerText.includes("hi")) {
        responseMood = "excited";
        response = "Hey there! Great to see you!";
      } else if (lowerText.includes("bye") || lowerText.includes("goodbye")) {
        responseMood = "sleepy";
        response = "See you later! Take care!";
      } else {
        responseMood = "happy";
        response = `I heard you say: "${text}"`;
      }

      setMood(responseMood);
      setIsSpeaking(true);
      setCurrentMessage({
        id: Date.now().toString(),
        text: response,
        from: "pal",
      });

      // Reset speaking state after animation
      setTimeout(() => setIsSpeaking(false), 250);
    }, 1200);
  }, []);

  return (
    <div className="chat-container">
      <div className="chat-container__face">
        <Face mood={mood} isThinking={isThinking} isSpeaking={isSpeaking} />
      </div>

      <div className="chat-container__message">
        <ChatMessage
          text={currentMessage?.text || ""}
          isThinking={isThinking}
        />
      </div>

      <div className="chat-container__input">
        <ChatInput onSend={handleSend} disabled={isThinking} />
      </div>
    </div>
  );
}

export default ChatContainer;
