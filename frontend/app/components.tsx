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

export const PromptSection: React.FC<PromptSectionProps> = ({ originalPrompt, inputValues, handleInputChange, keywords, gameEnded, lockedInputs }) => (
  <div className="flex flex-wrap gap-1 mb-2">
    {originalPrompt.split(/(\W+)/).map((word, idx) => {
      const lowerKeywords = keywords.map(keyword => keyword.toLowerCase());
      const wordLower = word.toLowerCase();
      const keywordIndex = lowerKeywords.indexOf(wordLower);
      if (keywordIndex !== -1) {
        const isLocked = lockedInputs[keywordIndex];
        const disabled = gameEnded || isLocked;
        const value = gameEnded ? keywords[keywordIndex] : (inputValues[keywordIndex] ?? "");
        return (
          <div key={idx} className="relative inline-block">
            <Input
              value={value}
              onChange={e => {
                if (!disabled) handleInputChange(keywordIndex, e.target.value);
              }}
              disabled={disabled}
              style={{ width: `${word.length + 1}ch` }}
            />
          </div>
        );
      } else {
        return (
          <span key={idx} className="text-sm inline-block align-middle">{word}</span>
        );
      }
    })}
  </div>
);

interface GuessHistorySectionProps {
  guessHistory: { word: string; color: string }[][];
}

export const GuessHistorySection: React.FC<GuessHistorySectionProps> = ({ guessHistory }) => (
  <div className="mt-4 space-y-2">
    {guessHistory.map((guess, roundIndex) => (
      <div key={roundIndex} className="flex gap-2">
        {guess.map((r, wordIndex) => {
          const variant = r.color === 'green' ? 'success' : 
                          r.color === 'yellow' ? 'warning' : 
                          r.color === 'red' ? 'destructive' : 'secondary';
          return (
            <Badge key={`${roundIndex}-${wordIndex}`} variant={variant}>
              {r.word}
            </Badge>
          );
        })}
      </div>
    ))}
  </div>
);

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
