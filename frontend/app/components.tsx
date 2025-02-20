import React from 'react';
import Image from 'next/image';

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
  <div className="mb-4">
    {image && (
      <Image
        src={image}
        alt="Guess the Prompt!"
        width={300}
        height={300}
      />
    )}
  </div>
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

interface GuessHistorySectionProps {
  guessHistory: { word: string; color: string }[][];
}

export const GuessHistorySection: React.FC<GuessHistorySectionProps> = ({ guessHistory }) => (
  <div className="mt-4 space-y-2">
    {guessHistory.map((guess, roundIndex) => (
      <div key={roundIndex} className="flex gap-2">
        {guess.map((r, wordIndex) => (
          <span
            key={`${roundIndex}-${wordIndex}`}
            className={`px-2 py-1 rounded ${
              r.color === "green" ? "bg-green-500" :
              r.color === "yellow" ? "bg-yellow-500" :
              r.color === "red" ? "bg-red-500" :
              "bg-gray-500"
            } text-white`}
          >
            {r.word}
          </span>
        ))}
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
    <button 
      onClick={copyToClipboard} 
      className="bg-blue-500 text-white p-2 rounded hover:bg-blue-600 mt-2"
    >
      Copy Recap to Clipboard
    </button>
  </div>
);
