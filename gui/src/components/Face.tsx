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

// Thinking face cycle - pondering expressions
const THINKING_FACES = [
  "(◕_◕)",    // neutral thinking
  "(◕.◕)",    // slight pause
  "( ◕_◕)",   // looking left
  "(◕_◕)",    // back to center
  "(◕_◕ )",   // looking right
  "(◕.◕)",    // pause again
];

function Face({ mood, isThinking = false, isSpeaking = false }: FaceProps) {
  const [isBlinking, setIsBlinking] = useState(false);
  const [isBouncing, setIsBouncing] = useState(false);
  const [thinkingIndex, setThinkingIndex] = useState(0);
  const blinkTimeoutRef = useRef<number | null>(null);
  const thinkingIntervalRef = useRef<number | null>(null);
  const speakingRef = useRef(false);

  // Cycle through thinking faces when thinking
  useEffect(() => {
    if (isThinking) {
      // Start cycling immediately
      setThinkingIndex(0);
      thinkingIntervalRef.current = window.setInterval(() => {
        setThinkingIndex((prev) => (prev + 1) % THINKING_FACES.length);
      }, 800); // ~0.8 second per expression for calm pondering
    } else {
      // Stop cycling when not thinking
      if (thinkingIntervalRef.current) {
        clearInterval(thinkingIntervalRef.current);
        thinkingIntervalRef.current = null;
      }
      setThinkingIndex(0);
    }

    return () => {
      if (thinkingIntervalRef.current) {
        clearInterval(thinkingIntervalRef.current);
      }
    };
  }, [isThinking]);

  // Get the current face based on mood and state
  const getDisplayFace = () => {
    if (isThinking) {
      return THINKING_FACES[thinkingIndex];
    }
    const baseFace = FACES[mood] || FACES.curious;
    const blinkFace = BLINK_FACES[mood] || BLINK_FACES.curious;
    return isBlinking ? blinkFace : baseFace;
  };

  const displayFace = getDisplayFace();

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
