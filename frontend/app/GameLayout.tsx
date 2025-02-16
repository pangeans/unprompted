'use client';
import { useState } from "react";
import { ImageSection, PromptSection, GuessHistorySection, GameOverSection } from "./components";
import { keywords, connectorWords, finalRoundChoices, originalPrompt, checkWord, generateRecap } from "./utils";

const GameLayout = () => {
  const [round, setRound] = useState(1);
  const [inputValues, setInputValues] = useState<string[]>(Array(5).fill(""));
  const [guessHistory, setGuessHistory] = useState<{ word: string; color: string }[][]>([]);
  const [gameEnded, setGameEnded] = useState(false);
  const [winningRound, setWinningRound] = useState<number | null>(null);

  const handleInputChange = (index: number, value: string) => {
    const newInputValues = [...inputValues];
    newInputValues[index] = value;
    setInputValues(newInputValues);
  };

  const handleSubmit = () => {
    if (gameEnded) return;

    const result: { word: string; color: string }[] = [];
    let keywordIndex = 0;

    inputValues.forEach((word, index) => {
      if (round <= 2) {
        result.push({ word, color: checkWord(word, keywords, index, round) });
      } else if (round <= 4) {
        if (connectorWords.includes(word)) {
          result.push({ word, color: "gray" });
        } else {
          result.push({ word, color: checkWord(word, keywords, keywordIndex++, round) });
        }
      } else {
        result.push({ word, color: checkWord(word, keywords, index, round) });
      }
    });

    setGuessHistory(prev => [...prev, result]);

    const greenMatches = result.filter(r => r.color === "green").length;
    if (round >= 5 || (greenMatches === keywords.length)) {
      setGameEnded(true);
      if (greenMatches === keywords.length) {
        setWinningRound(round);
      }
    } else {
      setRound(prev => prev + 1);
    }

    setInputValues(Array(5).fill(""));
  };

  const copyToClipboard = () => {
    const recap = generateRecap(guessHistory, round, winningRound);
    navigator.clipboard.writeText(recap);
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-8">
      <h1 className="text-2xl font-bold mb-4">unprompted.</h1>
      <ImageSection />
      <PromptSection
        originalPrompt={originalPrompt}
        inputValues={inputValues}
        handleInputChange={handleInputChange}
        keywords={keywords}
      />
      {!gameEnded && (
        <>
          <button 
            onClick={handleSubmit} 
            className="bg-blue-500 text-white p-2 rounded hover:bg-blue-600"
          >
            Submit
          </button>
        </>
      )}
      <div className="mt-4">
        <p>Round: {round}/5</p>
        <GuessHistorySection guessHistory={guessHistory} />
        {gameEnded && <GameOverSection winningRound={winningRound} copyToClipboard={copyToClipboard} />}
      </div>
    </div>
  );
};

export default GameLayout;