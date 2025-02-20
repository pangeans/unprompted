'use client';
import { useState, useEffect } from "react";
import { ImageSection, PromptSection, GuessHistorySection, GameOverSection } from "./components";
import { checkWord, generateRecap } from "./utils";

interface GameLayoutProps {
  randomIndex: number;
  image: string | null;
  prompt: string;
  keywords: string[];
}

const GameLayout: React.FC<GameLayoutProps> = ({ randomIndex, image, prompt, keywords }) => {
  const [round, setRound] = useState(1);
  const [inputValues, setInputValues] = useState<string[]>(Array(keywords.length).fill(""));
  const [lockedInputs, setLockedInputs] = useState<boolean[]>(Array(keywords.length).fill(false));
  const [guessHistory, setGuessHistory] = useState<{ word: string; color: string }[][]>([]);
  const [gameEnded, setGameEnded] = useState(false);
  const [winningRound, setWinningRound] = useState<number | null>(null);

  // Ensure state arrays update when keywords prop changes
  useEffect(() => {
    setInputValues(Array(keywords.length).fill(""));
    setLockedInputs(Array(keywords.length).fill(false));
  }, [keywords]);

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
        result.push({ word, color: checkWord(word, keywords, keywordIndex++, round) });
      } else {
        result.push({ word, color: checkWord(word, keywords, index, round) });
      }
    });

    // Update locked inputs for correctly guessed words
    const newLocked = [...lockedInputs];
    const newInputValues = [...inputValues];
    result.forEach((res, i) => {
      if (res.color === 'green') {
        newLocked[i] = true;
        // Fix the input to the correct keyword
        newInputValues[i] = keywords[i];
      }
    });

    setLockedInputs(newLocked);
    // Prepare next round's input: locked values remain, others empty
    const nextInputs = newLocked.map((locked, i) => locked ? newInputValues[i] : "");
    setInputValues(nextInputs);

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
  };

  const copyToClipboard = () => {
    const recap = generateRecap(randomIndex, guessHistory, round, winningRound);
    navigator.clipboard.writeText(recap);
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-8">
      <h1 className="text-2xl font-bold mb-4">unprompted.</h1>
      <ImageSection image={image} />
      <PromptSection
        originalPrompt={prompt}
        inputValues={inputValues}
        handleInputChange={handleInputChange}
        keywords={keywords}
        gameEnded={gameEnded}
        lockedInputs={lockedInputs}
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