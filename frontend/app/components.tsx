import React from 'react';
import Image from 'next/image';
import { cn } from '@/lib/utils';

// Import shadcn UI components
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

interface PromptSectionProps {
  originalPrompt: string;
  inputValues: string[];
  handleInputChange: (index: number, value: string) => void;
  keywords: string[];
  gameEnded: boolean;
  lockedInputs: boolean[];
  invalidInputs?: boolean[];
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

export const PromptSection: React.FC<PromptSectionProps> = ({ 
  originalPrompt, 
  inputValues, 
  handleInputChange, 
  keywords, 
  gameEnded, 
  lockedInputs,
  invalidInputs = Array(keywords.length).fill(false)
}) => {
  // Helper function to clean words for comparison
  const cleanWord = (word: string) => word.toLowerCase().trim().replace(/[.,!?]$/, '');
  
  // Split prompt into segments based on keyword positions
  const segments: { text: string, keywordIndex: number | null }[] = [];
  let currentText = '';
  
  const words = originalPrompt.split(/(\s+)/);
  for (let i = 0; i < words.length; i++) {
    const word = words[i];
    const keywordIndex = keywords.findIndex(k => cleanWord(k) === cleanWord(word));
    
    if (keywordIndex !== -1) {
      // If we have accumulated text, save it with the current keyword index
      if (currentText) {
        segments.push({ text: currentText, keywordIndex });
        currentText = '';
      }
    } else {
      currentText += word;
      // If this is the last word or next word is a keyword, save the segment
      if (i === words.length - 1 && currentText) {
        segments.push({ text: currentText, keywordIndex: null });
      }
    }
  }

  const renderInput = (index: number) => {
    const isLocked = lockedInputs[index];
    const disabled = gameEnded || isLocked;
    const value = inputValues[index] ?? "";
    const isEmpty = !value.trim();
    const isInvalid = invalidInputs[index];
    
    return (
      <div className={cn(
        "relative",
        "inline-block",
        "translate-y-1" // Adjust input position upward slightly
      )}>
        <input
          type="text"
          value={value}
          onChange={(e) => {
            if (!disabled) handleInputChange(index, e.target.value);
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !disabled) {
              e.preventDefault();
              const currentWord = cleanWord(value);
              const keyword = cleanWord(keywords[index]);
              if (currentWord === keyword) {
                handleInputChange(index, keywords[index]);
              }
              
              // Check if all fields are filled
              const allFilled = inputValues.every((val, idx) => 
                lockedInputs[idx] || val.trim().length > 0
              );

              if (allFilled) {
                const submitBtn = document.querySelector('button[type="submit"]');
                if (submitBtn instanceof HTMLButtonElement) submitBtn.click();
                return;
              }

              // Otherwise move to next input
              const nextIndex = lockedInputs.findIndex((locked, i) => !locked && i > index);
              if (nextIndex !== -1) {
                const nextInput = document.querySelector(`input[data-index="${nextIndex}"]`);
                if (nextInput instanceof HTMLInputElement) {
                  nextInput.focus();
                  nextInput.select();
                }
              }
            }
          }}
          disabled={disabled}
          data-index={index}
          placeholder="Type here..."
          className={cn(
            "px-2 py-1 rounded-md text-md min-w-fit not-italic",
            "transition-all duration-200 bg-transparent",
            {
              "bg-green-500 text-white font-bold": disabled && isLocked,
              "border-red-500 animate-shake": isInvalid,
              "empty:animate-pulse": isEmpty && !disabled,
              "ring-1 ring-muted/20": !disabled && !isInvalid,
            }
          )}
        />
        {!disabled && (
          <div 
            className={cn(
              "absolute bottom-0 left-0 w-full h-0.5 transform scale-x-0 transition-transform duration-200",
              "bg-blue-500",
              { "scale-x-100 animate-pulse": !isEmpty }
            )}
          />
        )}
      </div>
    );
  };

  return (
    <div className="flex flex-wrap gap-1 max-w-xl mx-auto text-md italic">
      {originalPrompt.split(/(\s+)/).map((word, idx) => {
        const keywordIndex = keywords.findIndex(k => cleanWord(k) === cleanWord(word));
        if (keywordIndex !== -1) {
          return <React.Fragment key={`input-${keywordIndex}-${idx}`}>
            {renderInput(keywordIndex)}
          </React.Fragment>;
        } else {
          return (
            <span key={`text-${idx}-${word}`} className="align-middle inline-block leading-10">
              {word}
            </span>
          );
        }
      })}
    </div>
  );
};

// Color interpolation helper
const interpolateColor = (score: number): string => {
  // HSL colors for better gradients
  if (score === 1) return 'hsl(142, 76%, 36%)'; // Perfect match green
  if (score >= 0.8) return `hsl(${120 * score}, 70%, 45%)`; // Green to yellow
  if (score >= 0.5) return `hsl(${120 * score}, 65%, 50%)`; // Yellow to orange
  return `hsl(0, 75%, ${45 + score * 20}%)`; // Red with varying lightness
};

interface GuessHistoryItem {
  word: string;
  score: number;
}

interface GuessHistorySectionProps {
  guessHistory: GuessHistoryItem[][];
  keywords: string[];
}

export const GuessHistorySection: React.FC<GuessHistorySectionProps> = ({ 
  guessHistory, 
  keywords
}) => {
  const cleanWord = (word: string) => word.toLowerCase().trim().replace(/[.,!?]$/, '');
  const totalRounds = 5;
  
  const boxClassName = "w-[100px] min-h-[40px] px-4 py-2 rounded flex flex-col items-center justify-center relative";

  return (
    <div className="mt-4 space-y-2.5 flex flex-col items-center">
      {Array(totalRounds).fill(null).map((_, roundIndex) => {
        const guess = guessHistory[roundIndex];
        
        return (
          <div key={`round-${roundIndex}`} className="flex gap-2.5">
            {guess ? (
              // Actual guesses
              guess.map((r, wordIndex) => {
                const score = typeof r.score === 'number' ? r.score : 0;
                const matching = cleanWord(r.word) === cleanWord(keywords[wordIndex]);
                const bgColor = interpolateColor(score);
                
                return (
                  <div 
                    key={`guess-${roundIndex}-${wordIndex}-${r.word}`}
                    className={cn(
                      boxClassName,
                      "text-white transition-all duration-300 break-words",
                      "hover:scale-105 transform",
                      matching ? "font-bold" : "font-normal"
                    )}
                    style={{ 
                      backgroundColor: bgColor,
                      opacity: 0.8 + score * 0.2
                    }}
                  >
                    <span className="relative z-10 text-center px-1">{r.word}</span>
                    <div className="absolute inset-x-0 bottom-0 h-1 bg-black/20">
                      <div 
                        className="h-full bg-white/80 transition-all duration-300"
                        style={{ width: `${score * 100}%` }}
                      />
                    </div>
                  </div>
                );
              })
            ) : (
              // Empty placeholder boxes
              keywords.map((_, wordIndex) => (
                <div 
                  key={`empty-${roundIndex}-${wordIndex}`}
                  className={cn(
                    boxClassName,
                    "bg-gray-500 opacity-30"
                  )}
                >
                  &nbsp;
                </div>
              ))
            )}
          </div>
        );
      })}
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
