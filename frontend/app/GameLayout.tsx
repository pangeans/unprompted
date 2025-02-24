'use client';
import { useState, useEffect } from "react";
import { ImageSection, PromptSection, GuessHistorySection, GameOverSection } from "./components";
import { Button } from "@/components/ui/button";
import { generateRecap } from "./utils";

interface GameLayoutProps {
  randomIndex: number;
  image: string | null;
  prompt: string;
  keywords: string[];
  similarityDict: Record<string, Record<string, number>>;
}

const GameLayout: React.FC<GameLayoutProps> = ({ randomIndex, image, prompt, keywords, similarityDict }) => {
  const [round, setRound] = useState(1);
  const [inputValues, setInputValues] = useState<string[]>(Array(keywords.length).fill(""));
  const [lockedInputs, setLockedInputs] = useState<boolean[]>(Array(keywords.length).fill(false));
  const [invalidInputs, setInvalidInputs] = useState<boolean[]>(Array(keywords.length).fill(false));
  const [guessHistory, setGuessHistory] = useState<{ word: string; score: number }[][]>([]);
  const [gameEnded, setGameEnded] = useState(false);
  const [winningRound, setWinningRound] = useState<number | null>(null);

  // Reset states when keywords change
  useEffect(() => {
    setInputValues(Array(keywords.length).fill(""));
    setLockedInputs(Array(keywords.length).fill(false));
    setInvalidInputs(Array(keywords.length).fill(false));
  }, [keywords]);

  const handleInputChange = (index: number, value: string) => {
    const newInputValues = [...inputValues];
    newInputValues[index] = value;
    setInputValues(newInputValues);

    // Clear invalid state when user types
    if (invalidInputs[index]) {
      const newInvalidInputs = [...invalidInputs];
      newInvalidInputs[index] = false;
      setInvalidInputs(newInvalidInputs);
    }
  };

  const handleSubmit = () => {
    if (gameEnded) return;

    // Check for empty fields
    const emptyFields = inputValues.map((value, index) => 
      !value.trim() && !lockedInputs[index]
    );
    
    if (emptyFields.some(isEmpty => isEmpty)) {
      setInvalidInputs(emptyFields);
      return;
    }

    const result: { word: string; score: number }[] = [];
    const newLocked = [...lockedInputs];
    const newInputValues = [...inputValues];

    // Helper function to clean words for comparison
    const cleanWord = (word: string) => word.toLowerCase().trim().replace(/[.,!?]$/, '');

    inputValues.forEach((word, index) => {
      let score = 0;
      const keyword = cleanWord(keywords[index]);
      const wordLower = cleanWord(word);
      
      // Check similarity dictionary with cleaned words
      const similarityEntry = similarityDict[keyword];
      if (similarityEntry) {
        // Try to find the score with the cleaned word
        for (const [dictWord, dictScore] of Object.entries(similarityEntry)) {
          if (cleanWord(dictWord) === wordLower) {
            score = dictScore;
            break;
          }
        }
      }

      result.push({ word, score });

      // Lock the input if it exactly matches the target keyword
      if (wordLower === keyword) {
        newLocked[index] = true;
        newInputValues[index] = keywords[index]; // Use original casing
      }
    });

    setLockedInputs(newLocked);
    
    // Prepare next round's inputs: locked values remain, others empty
    const nextInputs = newLocked.map((locked, i) => 
      locked ? newInputValues[i] : ""
    );
    setInputValues(nextInputs);
    setInvalidInputs(Array(keywords.length).fill(false)); // Reset invalid states

    setGuessHistory(prev => [...prev, result]);

    const greenMatches = newLocked.filter(locked => locked).length;
    if (round >= 5 || greenMatches === keywords.length) {
      setGameEnded(true);
      if (greenMatches === keywords.length) {
        setWinningRound(round);
      }
    } else {
      setRound(prev => prev + 1);
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
        invalidInputs={invalidInputs}
      />
      <Button 
        onClick={handleSubmit}
        type="submit"
        disabled={gameEnded || inputValues.some((value, index) => !value.trim() && !lockedInputs[index])}
        variant="default"
        size="lg"
        className="mt-2 hidden"
      >
        Submit
      </Button>
      <div className="w-full">
        <GuessHistorySection 
          guessHistory={guessHistory} 
          keywords={keywords}
        />
        {gameEnded && (
          <GameOverSection 
            winningRound={winningRound} 
            copyToClipboard={copyToClipboard} 
          />
        )}
      </div>
    </div>
  );
};

export default GameLayout;