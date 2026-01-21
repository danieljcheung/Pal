import { useState, useRef, useEffect, useImperativeHandle, forwardRef } from "react";
import "./ChatInput.css";

interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export interface ChatInputHandle {
  focus: () => void;
}

const ChatInput = forwardRef<ChatInputHandle, ChatInputProps>(
  ({ onSend, disabled = false }, ref) => {
    const [expanded, setExpanded] = useState(false);
    const [value, setValue] = useState("");
    const inputRef = useRef<HTMLInputElement>(null);

    // Expose focus method to parent
    useImperativeHandle(ref, () => ({
      focus: () => {
        if (!disabled) {
          setExpanded(true);
        }
      },
    }));

    // Focus input when expanded
    useEffect(() => {
      if (expanded && inputRef.current) {
        inputRef.current.focus();
      }
    }, [expanded]);

    const handleClick = () => {
      if (!expanded && !disabled) {
        setExpanded(true);
      }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && value.trim()) {
        onSend(value.trim());
        setValue("");
        setExpanded(false);
      } else if (e.key === "Escape") {
        setValue("");
        setExpanded(false);
      }
    };

    const handleBlur = () => {
      // Collapse if empty after a short delay
      setTimeout(() => {
        if (!value.trim()) {
          setExpanded(false);
        }
      }, 150);
    };

    return (
      <div
        className={`chat-input ${expanded ? "chat-input--expanded" : ""} ${disabled ? "chat-input--disabled" : ""}`}
        onClick={handleClick}
      >
        {expanded ? (
          <input
            ref={inputRef}
            type="text"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            onBlur={handleBlur}
            placeholder="Type a message..."
            disabled={disabled}
          />
        ) : (
          <span className="chat-input__placeholder">···</span>
        )}
      </div>
    );
  }
);

ChatInput.displayName = "ChatInput";

export default ChatInput;
