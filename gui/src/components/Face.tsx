interface FaceProps {
  mood: string;
}

// Kaomoji faces matching the Python backend
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

function Face({ mood }: FaceProps) {
  const face = FACES[mood] || FACES.curious;

  return <div className="face">{face}</div>;
}

export default Face;
