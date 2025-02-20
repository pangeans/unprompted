import React from 'react';
import Image from 'next/image';

interface PromptSectionProps {
  originalPrompt: string;
  inputValues: string[];
  handleInputChange: (index: number, value: string) => void;
  keywords: string[];
  gameEnded: boolean;
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

export const PromptSection: React.FC<PromptSectionProps> = ({ originalPrompt, inputValues, handleInputChange, keywords, gameEnded }) => (
  <div className="flex flex-wrap gap-1 mb-2">
    {originalPrompt.split(/(\W+)/).map((word, index) => (
      keywords.map(keyword => keyword.toLowerCase()).includes(word.toLowerCase()) ? (
        <div key={index} className="relative inline-block align-middle -translate-y-1">
          {gameEnded ? (
            <span className="bg-green-500 text-white p-1 rounded font-bold">{word}</span>
          ) : (
            <input
              type="text"
              value={inputValues[keywords.map(keyword => keyword.toLowerCase()).indexOf(word.toLowerCase())]}
              onChange={(e) => handleInputChange(keywords.map(keyword => keyword.toLowerCase()).indexOf(word.toLowerCase()), e.target.value)}
              className="p-1 text-black w-auto focus:outline-none focus:ring-0 border-0 caret-black text-sm align-middle "
              style={{ width: `${word.length + 1}ch` }}
            />
          )}
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
