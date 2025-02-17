import React from 'react';
import Image from 'next/image';

interface PromptSectionProps {
  originalPrompt: string;
  inputValues: string[];
  handleInputChange: (index: number, value: string) => void;
  keywords: string[];
}

export const ImageSection = () => (
  <div className="mb-4">
    <Image
      src="/jesus.webp"
      alt="AI generated"
      width={300}
      height={300}
    />
  </div>
);

export const PromptSection: React.FC<PromptSectionProps> = ({ originalPrompt, inputValues, handleInputChange, keywords }) => (
  <div className="flex flex-wrap gap-1 mb-2">
    {originalPrompt.split(/(\W+)/).map((word, index) => (
      keywords.includes(word) ? (
        <div key={index} className="relative inline-block align-middle -translate-y-1">
          <input
            type="text"
            value={inputValues[keywords.indexOf(word)]}
            onChange={(e) => handleInputChange(keywords.indexOf(word), e.target.value)}
            className="p-1 text-black w-auto focus:outline-none focus:ring-0 border-0 caret-black text-sm align-middle "
            style={{ width: `${word.length + 1}ch` }}
          />
          <div className="absolute bottom-0 left-0 w-full h-0.5 bg-black animate-flash"></div>
        </div>
      ) : (
        <span key={index} className="text-sm align-middle inline-block">{word}</span>
      )
    ))}
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
