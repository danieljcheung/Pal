import PixelFace from "./PixelFace";

interface FaceProps {
  mood: string;
  isThinking?: boolean;
  isSpeaking?: boolean;
}

/**
 * Face component - renders Pal's pixel art face
 * This is a wrapper around PixelFace for backwards compatibility
 */
function Face({ mood, isThinking = false, isSpeaking = false }: FaceProps) {
  return (
    <PixelFace mood={mood} isThinking={isThinking} isSpeaking={isSpeaking} />
  );
}

export default Face;
