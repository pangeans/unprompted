'use client';
import { useState, useEffect } from "react";
import { ImageSection, PromptSection, GuessHistorySection, GameOverSection } from "./components";
import { Button } from "@/components/ui/button";
import { generateRecap } from "./utils";

interface GameLayoutProps {
  randomIndex: number;
  image: string | null;
  originalImage: string; // Added original unblurred image
  blurPatternBase: string; // Added blur pattern base path
  prompt: string;
  keywords: string[];
  similarityDict: Record<string, Record<string, number>>;
  speechTypes?: string[];
}

const GameLayout: React.FC<GameLayoutProps> = ({ 
  randomIndex, 
  image, 
  originalImage, 
  blurPatternBase,
  prompt, 
  keywords, 
  similarityDict, 
  speechTypes = [] 
}) => {
  const [round, setRound] = useState(1);
  const [inputValues, setInputValues] = useState<string[]>(Array(keywords.length).fill(""));
  const [lockedInputs, setLockedInputs] = useState<boolean[]>(Array(keywords.length).fill(false));
  const [invalidInputs, setInvalidInputs] = useState<boolean[]>(Array(keywords.length).fill(false));
  const [guessHistory, setGuessHistory] = useState<{ word: string; score: number }[][]>([]);
  const [gameEnded, setGameEnded] = useState(false);
  const [winningRound, setWinningRound] = useState<number | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [currentImage, setCurrentImage] = useState<string | null>(image); // Track current image

  // Reset states when keywords change
  useEffect(() => {
    setInputValues(Array(keywords.length).fill(""));
    setLockedInputs(Array(keywords.length).fill(false));
    setInvalidInputs(Array(keywords.length).fill(false));
    setDialogOpen(false);
    setCurrentImage(image);
  }, [keywords, image]);

  // Show dialog when game ends
  useEffect(() => {
    if (gameEnded) {
      setDialogOpen(true);
      // If game ended, show original unblurred image
      setCurrentImage(originalImage);
    }
  }, [gameEnded, originalImage]);

  // Handle Enter key to reopen dialog
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Enter' && gameEnded && !dialogOpen) {
        setDialogOpen(true);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [gameEnded, dialogOpen]);

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

  // Function to update the current image based on guessed keywords
  const updateCurrentImage = (guessedIndices: number[]) => {
    // Create the filename parts for the blur pattern
    const blurParts: string[] = [];
    
    // For each keyword index
    for (let i = 0; i < keywords.length; i++) {
      // If the keyword is not guessed (locked), add it as a blurred part
      if (!guessedIndices.includes(i)) {
        blurParts.push(`${i}blur`);
      } else {
        // Otherwise add it as an unblurred part
        blurParts.push(`${i}`);
      }
    }
    
    // Sort the blur parts for consistency with how the filenames were generated
    blurParts.sort();
    
    // Construct the image path
    const newImagePath = `${blurPatternBase}${blurParts.join('_')}.webp`;
    setCurrentImage(newImagePath);
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
    const newlyCorrectIndices: number[] = [];

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
        if (!newLocked[index]) {
          newlyCorrectIndices.push(index); // Track newly correct guesses
        }
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

    // Get indices of all correctly guessed keywords
    const correctIndices = newLocked
      .map((locked, index) => locked ? index : -1)
      .filter(index => index !== -1);
    
    // Update the image if any new correct guesses were made
    if (newlyCorrectIndices.length > 0) {
      updateCurrentImage(correctIndices);
    }

    const greenMatches = newLocked.filter(locked => locked).length;
    if (round >= 5 || greenMatches === keywords.length) {
      setGameEnded(true);
      if (greenMatches === keywords.length) {
        setWinningRound(round);
      }
      // Game over - show original unblurred image
      setCurrentImage(originalImage);
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
      <ImageSection image={currentImage} />
      <PromptSection
        originalPrompt={prompt}
        inputValues={inputValues}
        handleInputChange={handleInputChange}
        keywords={keywords}
        gameEnded={gameEnded}
        lockedInputs={lockedInputs}
        invalidInputs={invalidInputs}
        speechTypes={speechTypes}
      />
      <Button 
        onClick={handleSubmit}
        type="submit"
        disabled={gameEnded || inputValues.some((value, index) => !value.trim() && !lockedInputs[index])}
        variant="default"
        size="lg"
        className="mt-4 mb-4 w-full sm:w-auto sm:hidden md:hidden lg:hidden xl:hidden"
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
            open={dialogOpen}
            onOpenChange={setDialogOpen}
            originalImage={originalImage}
            prompt={prompt}
          />
        )}
      </div>
    </div>
  );
};

export default GameLayout;