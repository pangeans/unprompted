import { useMemo } from 'react';
import { GAME_CONFIG } from '../constants';

interface GuessHistoryItem {
  word: string;
  score: number;
}

interface GuessHistorySectionProps {
  guessHistory: GuessHistoryItem[][];
  keywords: string[];
}

const memoizedInterpolateColor = (color1: {r: number, g: number, b: number}, color2: {r: number, g: number, b: number}, factor: number) => {
  const r = Math.round(color1.r + factor * (color2.r - color1.r));
  const g = Math.round(color1.g + factor * (color2.g - color1.g));
  const b = Math.round(color1.b + factor * (color2.b - color1.b));
  return `rgb(${r}, ${g}, ${b})`;
};

const getGradientColor = (score: number): string => {
  const { MIN, MAX, MID } = GAME_CONFIG.SCORE_THRESHOLDS;
  const { RED, YELLOW, GREEN } = GAME_CONFIG.COLORS;
  
  const normalized = Math.min(1, Math.max(0, (score - MIN) / (MAX - MIN)));
  
  if (normalized <= MID) {
    const factor = normalized / MID;
    return memoizedInterpolateColor(RED, YELLOW, factor);
  } else {
    const factor = (normalized - MID) / MID;
    return memoizedInterpolateColor(YELLOW, GREEN, factor);
  }
};

export const GuessHistorySection: React.FC<GuessHistorySectionProps> = ({ guessHistory, keywords }) => {
  const memoizedHistory = useMemo(() => 
    guessHistory.map((guess, roundIndex) => (
      <div key={roundIndex} className="flex gap-2">
        {guess.map((r, wordIndex) => {
          const score = typeof r.score === 'number' ? r.score : 0;
          const matching = r.word.toLowerCase() === keywords[wordIndex].toLowerCase();
          const bgColor = matching ? `rgb(${GAME_CONFIG.COLORS.GREEN.r}, ${GAME_CONFIG.COLORS.GREEN.g}, ${GAME_CONFIG.COLORS.GREEN.b})` : getGradientColor(score);
          
          return (
            <span
              key={`${roundIndex}-${wordIndex}`}
              className="px-2 py-1 rounded text-white"
              style={{ backgroundColor: bgColor }}
            >
              {r.word}
            </span>
          );
        })}
      </div>
    )), [guessHistory, keywords]
  );

  return (
    <div className="mt-4 space-y-2">
      {memoizedHistory}
    </div>
  );
};