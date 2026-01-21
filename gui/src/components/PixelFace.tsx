import { useEffect, useState, useRef } from "react";
import "./PixelFace.css";

interface PixelFaceProps {
  mood: string;
  isThinking?: boolean;
  isSpeaking?: boolean;
}

// Unicode cat faces for each mood
const FACES: Record<string, string> = {
  happy: "ᴖ ﻌ ᴖ",
  curious: "ᴖ ᴑ ᴖ",
  excited: "ᴗ ▽ ᴗ",
  thinking: "– ﻌ –",
  confused: "ᴖ ～ ᴖ",
  sad: "ᵕ ︵ ᵕ",
  worried: "ᵕ ︵ ᵕ",
  sleepy: "– ᵕ –",
};

// Blink face
const BLINK_FACE = "– ᵕ –";

function PixelFace({ mood, isThinking = false, isSpeaking = false }: PixelFaceProps) {
  const [isBlinking, setIsBlinking] = useState(false);
  const [isBouncing, setIsBouncing] = useState(false);
  const [displayFace, setDisplayFace] = useState(FACES.curious);
  const blinkTimeoutRef = useRef<number | null>(null);
  const speakingRef = useRef(false);

  // Update face when mood changes (with fade)
  useEffect(() => {
    const currentMood = isThinking ? "thinking" : mood;
    const newFace = FACES[currentMood] || FACES.curious;
    setDisplayFace(newFace);
  }, [mood, isThinking]);

  // Blinking effect
  useEffect(() => {
    const scheduleBlink = () => {
      const delay = 3000 + Math.random() * 2000;
      blinkTimeoutRef.current = window.setTimeout(() => {
        setIsBlinking(true);
        setTimeout(() => {
          setIsBlinking(false);
          scheduleBlink();
        }, 150);
      }, delay);
    };

    scheduleBlink();
    return () => {
      if (blinkTimeoutRef.current) clearTimeout(blinkTimeoutRef.current);
    };
  }, []);

  // Bounce on speaking
  useEffect(() => {
    if (isSpeaking && !speakingRef.current) {
      setIsBouncing(true);
      setTimeout(() => setIsBouncing(false), 200);
    }
    speakingRef.current = isSpeaking;
  }, [isSpeaking]);

  // Determine which face to show
  const faceToShow = isBlinking ? BLINK_FACE : displayFace;

  const classNames = [
    "unicode-face",
    isThinking ? "unicode-face--thinking" : "",
    isBouncing ? "unicode-face--bounce" : "",
  ].filter(Boolean).join(" ");

  return (
    <div className={classNames}>
      <span className="unicode-face__text">{faceToShow}</span>
    </div>
  );
}

export default PixelFace;
