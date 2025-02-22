'use client';
import { useState, useEffect } from "react";
import { ImageSection, PromptSection, GuessHistorySection, GameOverSection } from "./components";
import { generateRecap } from "./utils";

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
  const [guessHistory, setGuessHistory] = useState<{ word: string; score: number }[][]>([]);
  const [gameEnded, setGameEnded] = useState(false);
  const [winningRound, setWinningRound] = useState<number | null>(null);
  const [simMappings, setSimMappings] = useState<{ [key: string]: Record<string, number> }>({});

  // Ensure state arrays update when keywords prop changes
  useEffect(() => {
    setInputValues(Array(keywords.length).fill(""));
    setLockedInputs(Array(keywords.length).fill(false));
  }, [keywords]);

  // Fetch the JSON mapping for each keyword on mount inside GameLayout
  useEffect(() => {
    async function fetchMappings() {
      const mappings: { [key: string]: Record<string, number> } = {};
      await Promise.all(keywords.map(async (keyword) => {
        try {
          const res = await fetch(`/${keyword.toLowerCase()}.json`);
          if (res.ok) {
            mappings[keyword] = await res.json();
          }
        } catch (err) {
          console.error(`Error loading mapping for ${keyword}:`, err);
        }
      }));
      setSimMappings(mappings);
    }
    fetchMappings();
  }, [keywords]);

  const handleInputChange = (index: number, value: string) => {
    const newInputValues = [...inputValues];
    newInputValues[index] = value;
    setInputValues(newInputValues);
  };

  const handleSubmit = () => {
    if (gameEnded) return;

    const result: { word: string; score: number }[] = [];
    const newLocked = [...lockedInputs];
    const newInputValues = [...inputValues];

    inputValues.forEach((word, index) => {
      const mapping = simMappings[keywords[index]];
      let score = 0;
      if (mapping && mapping[word.toLowerCase()] !== undefined) {
        score = mapping[word.toLowerCase()];
      }
      result.push({ word, score });

      // Lock the input if it exactly matches the target keyword
      if (word.toLowerCase() === keywords[index].toLowerCase()) {
        newLocked[index] = true;
        newInputValues[index] = keywords[index];
      }
    });

    setLockedInputs(newLocked);
    // Prepare next round's inputs: locked values remain, others empty
    const nextInputs = newLocked.map((locked, i) => (locked ? newInputValues[i] : ""));
    setInputValues(nextInputs);

    setGuessHistory((prev) => [...prev, result]);

    const greenMatches = newLocked.filter((locked) => locked).length;
    if (round >= 5 || greenMatches === keywords.length) {
      setGameEnded(true);
      if (greenMatches === keywords.length) {
        setWinningRound(round);
      }
    } else {
      setRound((prev) => prev + 1);
    }
  };

  const copyToClipboard = () => {
    const recap = generateRecap(randomIndex, guessHistory, round);
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
        <GuessHistorySection guessHistory={guessHistory} keywords={keywords} />
        {gameEnded && <GameOverSection winningRound={winningRound} copyToClipboard={copyToClipboard} />}
      </div>
    </div>
  );
};

export default GameLayout;