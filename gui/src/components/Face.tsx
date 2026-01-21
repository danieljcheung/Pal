import { useEffect, useState, useRef } from "react";
import "./Face.css";

interface FaceProps {
  mood: string;
  isThinking?: boolean;
  isSpeaking?: boolean;
}

const FACES: Record<string, string> = {
  happy: "(◕‿◕)",
  curious: "(◕ᴗ◕)?",
  excited: "(◕▽◕)!",
  thinking: "(◕_◕)",
  confused: "(◕~◕)?",
  sad: "(◕︵◕)",
  worried: "(◕︿◕)",
  sleepy: "(◡‿◡)",
};

// Faces with blink state (eyes replaced with ─)
const BLINK_FACES: Record<string, string> = {
  happy: "(─‿─)",
  curious: "(─ᴗ─)?",
  excited: "(─▽─)!",
  thinking: "(─_─)",
  confused: "(─~─)?",
  sad: "(─︵─)",
  worried: "(─︿─)",
  sleepy: "(─‿─)",
};

function Face({ mood, isThinking = false, isSpeaking = false }: FaceProps) {
  const [isBlinking, setIsBlinking] = useState(false);
  const [isBouncing, setIsBouncing] = useState(false);
  const blinkTimeoutRef = useRef<number | null>(null);
  const speakingRef = useRef(false);

  // Get the current face based on mood and blink state
  const currentMood = isThinking ? "thinking" : mood;
  const baseFace = FACES[currentMood] || FACES.curious;
  const blinkFace = BLINK_FACES[currentMood] || BLINK_FACES.curious;
  const displayFace = isBlinking ? blinkFace : baseFace;

  // Blinking effect - randomized interval between 3-5 seconds
  useEffect(() => {
    const scheduleBlink = () => {
      const delay = 3000 + Math.random() * 2000; // 3-5 seconds
      blinkTimeoutRef.current = window.setTimeout(() => {
        setIsBlinking(true);
        // Blink duration ~150ms
        setTimeout(() => {
          setIsBlinking(false);
          scheduleBlink();
        }, 150);
      }, delay);
    };

    scheduleBlink();

    return () => {
      if (blinkTimeoutRef.current) {
        clearTimeout(blinkTimeoutRef.current);
      }
    };
  }, []);

  // Bounce effect when speaking starts
  useEffect(() => {
    if (isSpeaking && !speakingRef.current) {
      setIsBouncing(true);
      setTimeout(() => setIsBouncing(false), 200);
    }
    speakingRef.current = isSpeaking;
  }, [isSpeaking]);

  const classNames = [
    "face",
    isThinking ? "face--thinking" : "",
    isBouncing ? "face--bounce" : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={classNames}>
      <span className="face__text">{displayFace}</span>
    </div>
  );
}

export default Face;
