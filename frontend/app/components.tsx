import React, { useState, useEffect } from 'react';
import Image from 'next/image';
import { cn } from '@/lib/utils';

// Import shadcn UI components
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { getNextGameTime, formatTimeRemaining } from './utils';

interface PromptSectionProps {
  originalPrompt: string;
  inputValues: string[];
  handleInputChange: (index: number, value: string) => void;
  keywords: string[];
  gameEnded: boolean;
  lockedInputs: boolean[];
  invalidInputs?: boolean[];
  speechTypes?: string[]; // Add speech types prop
}

interface MediaSectionProps {
  media: string | null;
  isVideo?: boolean;
}

export const MediaSection: React.FC<MediaSectionProps> = ({ media, isVideo = false }) => {
  // If we don't have media yet, show a placeholder
  if (!media) {
    return (
      <Card className="mb-4 overflow-hidden">
        <CardContent className="p-0 relative">
          <div className="w-[500px] h-[500px] bg-gray-200 animate-pulse" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="mb-4 overflow-hidden">
      <CardContent className="p-0">
        <div className="relative w-[500px] h-[500px] flex items-center justify-center bg-black/5">
          {isVideo ? (
            <video 
              src={media}
              autoPlay
              loop
              muted
              playsInline
              className="absolute inset-0 w-full h-full transition-opacity duration-300"
              style={{ objectFit: 'contain', opacity: 0 }}
              onLoadedData={(e) => {
                const video = e.currentTarget;
                video.style.opacity = '1';
              }}
            />
          ) : (
            <div className="absolute inset-0 w-full h-full transition-opacity duration-300">
              <Image
                src={media}
                alt="Guess the Prompt!"
                fill
                sizes="500px"
                className="object-contain"
                priority
                style={{ transition: 'filter 0.3s ease-in-out' }}
                onLoadingComplete={(img) => {
                  // Add a small delay to ensure the new image is ready
                  setTimeout(() => {
                    img.style.opacity = '1';
                  }, 50);
                }}
              />
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export const PromptSection: React.FC<PromptSectionProps> = ({ 
  originalPrompt, 
  inputValues, 
  handleInputChange, 
  keywords, 
  gameEnded, 
  lockedInputs,
  invalidInputs = Array(keywords.length).fill(false),
  speechTypes = Array(keywords.length).fill("") // Default to empty speech types
}) => {
  // Helper function to clean words for comparison
  const cleanWord = (word: string) => word.toLowerCase().trim().replace(/[.,!?]$/, '');
  
  // Function to get placeholder based on speech type
  const getPlaceholderFromSpeechType = (speechType: string) => {
    switch(speechType?.toLowerCase()) {
      case 'noun': return "noun...";
      case 'verb': return "verb...";
      case 'adverb': return "adverb...";
      case 'adjective': return "adjective...";
      default: return "Type here...";
    }
  };
  
  // Function to get background color based on speech type
  const getSpeechTypeColor = (speechType: string) => {
    switch(speechType?.toLowerCase()) {
      case 'noun': return "rgba(59, 130, 246, 0.1)"; // blue tint
      case 'verb': return "rgba(16, 185, 129, 0.1)"; // green tint
      case 'adverb': return "rgba(245, 158, 11, 0.1)"; // amber tint
      case 'adjective': return "rgba(239, 68, 68, 0.1)"; // red tint
      default: return "transparent";
    }
  };
  
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
    const targetWord = keywords[index];
    const speechType = speechTypes[index] || "";
    const minWidth = Math.max(targetWord.length * 0.85 + 1, 4) + 'em'; // Added 1em padding and increased minimum
    
    // Set placeholder based on speech type
    const placeholder = getPlaceholderFromSpeechType(speechType);
    
    // Set background color based on speech type
    const speechTypeColor = getSpeechTypeColor(speechType);
    
    return (
      <div className={cn(
        "relative",
        "inline-block",
        "translate-y-1" // Adjust input position upward slightly
      )}>
        <input
          type="text"
          value={gameEnded && !isLocked ? targetWord : value} // Show correct word when game ends and input is not locked
          style={{ 
            width: minWidth,
            backgroundColor: (disabled && isLocked) ? '#238c47' : speechTypeColor
            // Using hex color #238c47 instead of hsl(142,76%,36%) for consistent rendering
          }}
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

              // Find next unlocked input, wrapping around to the beginning
              const nextIndex = lockedInputs.findIndex((locked, i) => !locked && i > index);
              const firstUnlockedIndex = lockedInputs.findIndex(locked => !locked);
              const targetIndex = nextIndex !== -1 ? nextIndex : firstUnlockedIndex;
              
              if (targetIndex !== -1) {
                const nextInput = document.querySelector(`input[data-index="${targetIndex}"]`);
                if (nextInput instanceof HTMLInputElement) {
                  nextInput.focus();
                  nextInput.select();
                }
              }
            }
          }}
          disabled={disabled}
          data-index={index}
          placeholder={placeholder}
          className={cn(
            "px-3 py-1 rounded-md text-md not-italic",
            "transition-all duration-200 bg-transparent text-center",
            {
              "text-white font-bold": disabled && isLocked,
              "bg-red-500 text-white font-bold": gameEnded && !isLocked, // Red background for incorrect answers when game ends
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
  if (score === 1) return '#238c47'; // Using hex color instead of HSL for consistent rendering
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
  previousGameSquares?: string | null;
  alreadyPlayed?: boolean;
}

export const GuessHistorySection: React.FC<GuessHistorySectionProps> = ({ 
  guessHistory, 
  keywords,
  previousGameSquares = null,
  alreadyPlayed = false
}) => {
  const cleanWord = (word: string) => word.toLowerCase().trim().replace(/[.,!?]$/, '');
  const totalRounds = 5;
  
  // Modified class to reduce padding, prevent text wrapping, and use smaller font size
  const boxClassName = "w-[calc((85vw-1.5rem)/3)] sm:w-[100px] min-h-[36px] sm:min-h-[40px] px-1 sm:px-2 py-1 sm:py-1.5 rounded flex flex-col items-center justify-center relative text-xs sm:text-sm";

  // If we have previous game squares and this is a returning player,
  // parse and display those instead of the current game state
  if (alreadyPlayed && previousGameSquares) {
    const squareRows = previousGameSquares.trim().split('\n');
    
    return (
      <div className="mt-4 space-y-2 sm:space-y-2.5 flex flex-col items-center w-[85vw] mx-auto">
        {squareRows.map((row, rowIndex) => (
          <div key={`prev-round-${rowIndex}`} className="flex gap-2 sm:gap-2.5 w-full justify-center">
            {Array.from(row).map((square, squareIndex) => {
              // Determine color based on emoji
              const bgColor = square === "🟩" 
                ? "#238c47" 
                : square === "🟨" 
                  ? "hsl(48, 65%, 50%)" 
                  : "hsl(0, 0%, 40%)";
              
              return (
                <div 
                  key={`prev-square-${rowIndex}-${squareIndex}`}
                  className={cn(
                    boxClassName,
                    "text-white transition-all duration-300 flex items-center justify-center"
                  )}
                  style={{ backgroundColor: bgColor }}
                >
                  <span className="text-xl">{square}</span>
                </div>
              );
            })}
            
            {/* Fill remaining boxes if row has fewer squares than keywords */}
            {row.length < keywords.length && Array(keywords.length - row.length).fill(null).map((_, i) => (
              <div 
                key={`empty-prev-${rowIndex}-${i}`}
                className={cn(
                  boxClassName,
                  "bg-gray-500 opacity-30"
                )}
              >
                &nbsp;
              </div>
            ))}
          </div>
        ))}
        
        {/* Fill remaining rows if we have fewer rows than totalRounds */}
        {squareRows.length < totalRounds && Array(totalRounds - squareRows.length).fill(null).map((_, rowIndex) => (
          <div key={`empty-prev-row-${rowIndex}`} className="flex gap-2 sm:gap-2.5 w-full justify-center">
            {keywords.map((_, wordIndex) => (
              <div 
                key={`empty-prev-${rowIndex + squareRows.length}-${wordIndex}`}
                className={cn(
                  boxClassName,
                  "bg-gray-500 opacity-30"
                )}
              >
                &nbsp;
              </div>
            ))}
          </div>
        ))}
      </div>
    );
  }

  // Default rendering for active game
  return (
    <div className="mt-4 space-y-2 sm:space-y-2.5 flex flex-col items-center w-[85vw] mx-auto">
      {Array(totalRounds).fill(null).map((_, roundIndex) => {
        const guess = guessHistory[roundIndex];
        
        return (
          <div key={`round-${roundIndex}`} className="flex gap-2 sm:gap-2.5 w-full justify-center">
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
                      "text-white transition-all duration-300",
                      "hover:scale-105 transform",
                      matching ? "font-bold" : "font-normal"
                    )}
                    style={{ 
                      backgroundColor: bgColor,
                      opacity: 0.8 + score * 0.2
                    }}
                  >
                    {/* Added whitespace-nowrap, overflow-hidden, and text-ellipsis for text overflow */}
                    <span className="relative z-10 text-center px-0.5 leading-tight whitespace-nowrap overflow-hidden text-ellipsis max-w-full">{r.word}</span>
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
  open: boolean;
  onOpenChange: (open: boolean) => void;
  finalMedia?: string | null;
  isVideo?: boolean;
  alreadyPlayed?: boolean;
}

export const GameOverSection: React.FC<GameOverSectionProps> = ({ 
  winningRound, 
  copyToClipboard, 
  open, 
  onOpenChange,
  finalMedia,
  isVideo = false,
  alreadyPlayed = false
}) => {
  const [nextGameTime, setNextGameTime] = useState<Date | null>(null);
  const [timeRemaining, setTimeRemaining] = useState<string>('');
  
  // Fetch next game time when component mounts
  useEffect(() => {
    const fetchNextGame = async () => {
      const time = await getNextGameTime();
      setNextGameTime(time);
      
      if (time) {
        setTimeRemaining(formatTimeRemaining(time));
      }
    };
    
    fetchNextGame();
    
    // Update the countdown every minute
    const intervalId = setInterval(() => {
      if (nextGameTime) {
        setTimeRemaining(formatTimeRemaining(nextGameTime));
      }
    }, 60000); // Update every minute
    
    return () => clearInterval(intervalId);
  }, [nextGameTime]); // Added nextGameTime to dependency array
  
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold text-center">Game Over!</DialogTitle>
          <div className="text-center">
            {alreadyPlayed ? (
              <p className="text-lg mb-2">You&apos;ve already played today&apos;s game.</p>
            ) : winningRound !== null ? (
              <p className="text-lg mb-2">You won in round {winningRound}! 🎉</p>
            ) : (
              <p className="text-lg mb-2">Better luck next time!</p>
            )}
          </div>
        </DialogHeader>
        
        {/* Final unpixelated media */}
        {finalMedia && (
          <div className="my-4 flex justify-center">
            <Card className="overflow-hidden">
              <CardContent className="p-0">
                <div className="relative w-[300px] h-[300px] flex items-center justify-center bg-black/5">
                  {isVideo ? (
                    <video
                      src={finalMedia}
                      autoPlay
                      loop
                      muted
                      playsInline
                      className="absolute inset-0 w-full h-full transition-opacity duration-300"
                      style={{ objectFit: 'contain', opacity: 0 }}
                      onLoadedData={(e) => {
                        const video = e.currentTarget;
                        video.style.opacity = '1';
                      }}
                    />
                  ) : (
                    <div className="absolute inset-0 w-full h-full transition-opacity duration-300">
                      <Image
                        src={finalMedia}
                        alt="Final Image"
                        fill
                        sizes="300px"
                        className="object-contain"
                        style={{ transition: 'filter 0.3s ease-in-out' }}
                        onLoadingComplete={(img) => {
                          setTimeout(() => {
                            img.style.opacity = '1';
                          }, 50);
                        }}
                      />
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        )}
        
        {/* Next game timer */}
        <div className="text-center mt-2 mb-2">
          <h3 className="text-sm font-semibold mb-1">Next game:</h3>
          {nextGameTime ? (
            <p className="text-lg font-bold">{timeRemaining}</p>
          ) : (
            <p className="text-lg text-gray-600">No games currently scheduled.</p>
          )}
        </div>
        
        <Button onClick={copyToClipboard} className="w-full mt-4">
          Copy Recap to Clipboard
        </Button>
      </DialogContent>
    </Dialog>
  );
};
