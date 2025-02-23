import React from 'react';
import Image from 'next/image';

// Import shadcn UI components
import { Card, CardContent } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

interface PromptSectionProps {
  originalPrompt: string;
  inputValues: string[];
  handleInputChange: (index: number, value: string) => void;
  keywords: string[];
  gameEnded: boolean;
  lockedInputs: boolean[];
}

interface ImageSectionProps {
  image: string | null;
}

export const ImageSection: React.FC<ImageSectionProps> = ({ image }) => (
  <Card className="mb-4">
    <CardContent className="p-0">
      {image && (
        <Image
          src={image}
          alt="Guess the Prompt!"
          width={300}
          height={300}
        />
      )}
    </CardContent>
  </Card>
);

export const PromptSection: React.FC<PromptSectionProps> = ({ originalPrompt, inputValues, handleInputChange, keywords, gameEnded, lockedInputs }) => {
  return (
    <div className="flex flex-wrap gap-1 mb-2">
      {originalPrompt.split(/(\W+)/).map((word, idx) => {
        const lowerKeywords = keywords.map(keyword => keyword.toLowerCase());
        const wordLower = word.toLowerCase();
        const keywordIndex = lowerKeywords.indexOf(wordLower);
        if (keywordIndex !== -1) {
          const isLocked = lockedInputs[keywordIndex];
          const disabled = gameEnded || isLocked;
          const value = gameEnded ? keywords[keywordIndex] : (inputValues[keywordIndex] ?? "");
        const styleClass = gameEnded ? (isLocked ? "bg-green-500 text-white p-1 rounded font-bold" : "bg-red-500 text-white p-1 rounded font-bold") : (isLocked ? "bg-green-500 text-white p-1 rounded font-bold" : "p-1 text-black w-auto focus:outline-none focus:ring-0 border-0 caret-black text-sm align-middle");
          return (
            <div key={idx} className="relative inline-block align-middle -translate-y-1">
              <input
                type="text"
                value={value}
                onChange={e => {
if (!disabled) handleInputChange(keywordIndex, e.target.value);
}}
                disabled={disabled}
                className={styleClass}
              style={{ width: `${word.length + 1}ch` }}
              />
              {!disabled && <div className="absolute bottom-0 left-0 w-full h-0.5 bg-black animate-flash"></div>}
            </div>
          );
        } else {
          return (
            <span key={idx} className="text-sm align-middle inline-block">{word}</span>
          );
        }
      })}
    </div>
  );
};

// Extract common color helper functions
export const interpolateColor = (color1: {r: number, g: number, b: number}, color2: {r: number, g: number, b: number}, factor: number) => {
  const r = Math.round(color1.r + factor * (color2.r - color1.r));
  const g = Math.round(color1.g + factor * (color2.g - color1.g));
  const b = Math.round(color1.b + factor * (color2.b - color1.b));
  return `rgb(${r}, ${g}, ${b})`;
};

// Updated getGradientColor function for GuessHistorySection with adjusted thresholds
export const getGradientColor = (score: number): string => {
  // Adjusted expected score range for normalization: from 0.0 (red) to 0.7 (green)
  const minThreshold = 0.0;
  const maxThreshold = 1.0;
  // Normalize the score to a 0-1 range based on the threshold
  const normalized = Math.min(1, Math.max(0, (score - minThreshold) / (maxThreshold - minThreshold)));

  const red = { r: 239, g: 68, b: 68 };        // Tailwind red-500 (#ef4444)
  const yellow = { r: 245, g: 158, b: 11 };      // Tailwind yellow-500 (#f59e0b)
  const green = { r: 34, g: 197, b: 94 };         // Tailwind green-500 (#22c55e)
  console.log(`Score: ${score}, Normalized: ${normalized}`);
  if (normalized <= 0.5) {
    const factor = normalized / 0.5; // 0 -> red, 1 -> yellow
    return interpolateColor(red, yellow, factor);
  } else {
    const factor = (normalized - 0.5) / 0.5; // 0 -> yellow, 1 -> green
    return interpolateColor(yellow, green, factor);
  }
};

// Update GuessHistorySection by updating the interface and component
interface GuessHistoryItem {
  word: string;
  score: number;
}

interface GuessHistorySectionProps {
  guessHistory: GuessHistoryItem[][];
  keywords: string[];
}

// Remove simMappings state and its useEffect as they are no longer used
export const GuessHistorySection: React.FC<GuessHistorySectionProps> = ({ guessHistory, keywords }) => {
  return (
    <div className="mt-4 space-y-2">
      {guessHistory.map((guess, roundIndex) => (
        <div key={roundIndex} className="flex gap-2">
          {guess.map((r, wordIndex) => {
            const score = typeof r.score === 'number' ? r.score : 0;
            // If the guessed word matches its corresponding keyword exactly (ignoring case), use green color
            const matching = r.word.toLowerCase() === keywords[wordIndex].toLowerCase();
            const bgColor = matching ? 'rgb(34, 197, 94)' : getGradientColor(score);
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
      ))}
    </div>
  );
};

interface GameOverSectionProps {
  winningRound: number | null;
  copyToClipboard: () => void;
}

export const GameOverSection: React.FC<GameOverSectionProps> = ({ winningRound, copyToClipboard }) => (
  <div className="mt-4">
    <p className="text-xl font-bold">Game Over!</p>
    {winningRound !== null && <p>You won in round {winningRound}!</p>}
    <Button onClick={copyToClipboard} className="mt-2">
      Copy Recap to Clipboard
    </Button>
  </div>
);
