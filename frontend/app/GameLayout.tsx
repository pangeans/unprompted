'use client';
import { useState, useEffect, useCallback } from "react";
import { MediaSection, PromptSection, GuessHistorySection, GameOverSection } from "./components";
import { Button } from "@/components/ui/button";
import { generateRecap } from "./utils";

interface GameLayoutProps {
  randomIndex: number;
  image: string | null;
  prompt: string;
  keywords: string[];
  similarityDict: Record<string, Record<string, number>>;
  speechTypes?: string[];
  pixelationMap?: Record<string, string> | null;
  isLoading?: boolean;
  isVideo?: boolean;
}

const GameLayout: React.FC<GameLayoutProps> = ({ 
  randomIndex, 
  image, 
  prompt, 
  keywords, 
  similarityDict, 
  speechTypes = [],
  pixelationMap = null,
  isLoading = false,
  isVideo = false
}) => {
  const [round, setRound] = useState(1);
  const [inputValues, setInputValues] = useState<string[]>(Array(keywords.length).fill(""));
  const [lockedInputs, setLockedInputs] = useState<boolean[]>(Array(keywords.length).fill(false));
  const [invalidInputs, setInvalidInputs] = useState<boolean[]>(Array(keywords.length).fill(false));
  const [guessHistory, setGuessHistory] = useState<{ word: string; score: number }[][]>([]);
  const [gameEnded, setGameEnded] = useState(false);
  const [winningRound, setWinningRound] = useState<number | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  
  // State for current displayed image
  const [currentImage, setCurrentImage] = useState<string | null>(null);

  // Helper function to get image key from locked inputs
  const getImageKeyFromLocked = useCallback((locked: boolean[]) => {
    if (!pixelationMap || Object.keys(pixelationMap).length === 0) {
      return null;
    }
    
    // Create a key for the image based on which keywords are unlocked
    const imageParts = locked.map((isLocked, index) => 
      isLocked ? `${index}` : `${index}blur`
    );
    
    // Use .mp4 extension for videos, .webp for images
    const extension = isVideo ? '.mp4' : '.webp';
    const keyToFind = imageParts.join('_') + extension;
    console.log("Looking for image/video key:", keyToFind);
    console.log("Locked state:", locked);
    
    return keyToFind;
  }, [pixelationMap, isVideo]);

  // Helper function to update the current image based on locked state
  const updateCurrentImageFromLocked = useCallback((locked: boolean[]) => {
    // Use the original image if game is ended
    if (gameEnded && image) {
      console.log("Game ended - showing original image");
      setCurrentImage(image);
      return;
    }
    
    // If we have a pixelation map, use it to select the right image
    if (pixelationMap && Object.keys(pixelationMap).length > 0) {
      const imageKey = getImageKeyFromLocked(locked);
      
      if (imageKey && pixelationMap[imageKey]) {
        console.log("Found matching image key:", imageKey);
        setCurrentImage(pixelationMap[imageKey]);
      } else {
        // If no matching key is found, try to find the fully pixelated image
        console.log("No matching key found, looking for fully pixelated image");
        // Find a key where all segments are pixelated
        const allPixelatedKey = Object.keys(pixelationMap).find(key => 
          keywords.every((_, i) => key.includes(`${i}blur`))
        );
        
        if (allPixelatedKey) {
          console.log("Using fully pixelated image:", allPixelatedKey);
          setCurrentImage(pixelationMap[allPixelatedKey]);
        } else {
          // Fallback to original image if no pixelated images are found
          console.log("No pixelated images found, using original image");
          setCurrentImage(image);
        }
      }
    } else {
      // No pixelation map, use the original image
      console.log("No pixelation map, using original image");
      setCurrentImage(image);
    }
  }, [gameEnded, image, pixelationMap, keywords, getImageKeyFromLocked]);

  // Find the fully pixelated image key on initial load
  useEffect(() => {
    if (pixelationMap && Object.keys(pixelationMap).length > 0 && keywords.length > 0) {
      // Find a key where all segments are pixelated
      const allBlurred = Array(keywords.length).fill(false);
      updateCurrentImageFromLocked(allBlurred);
    } else {
      // No pixelation map, use the original image
      setCurrentImage(image);
    }
  }, [pixelationMap, keywords, image, updateCurrentImageFromLocked]);

  // Update current image whenever locked inputs change
  useEffect(() => {
    updateCurrentImageFromLocked(lockedInputs);
  }, [lockedInputs, updateCurrentImageFromLocked]);

  // Rest of the code remains the same...
  
  // Reset states when keywords change
  useEffect(() => {
    setInputValues(Array(keywords.length).fill(""));
    setLockedInputs(Array(keywords.length).fill(false));
    setInvalidInputs(Array(keywords.length).fill(false));
    setDialogOpen(false);
    setRound(1);
    setGuessHistory([]);
    setGameEnded(false);
    setWinningRound(null);
  }, [keywords]);

  // Show dialog when game ends
  useEffect(() => {
    if (gameEnded) {
      setDialogOpen(true);
    }
  }, [gameEnded]);

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
      if (lockedInputs[index]) {
        // Keep previously correct answers
        result.push({ word: keywords[index], score: 1 });
        return;
      }

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
        console.log(`Correct guess for keyword ${index}: "${keyword}"`);
        newLocked[index] = true;
        newInputValues[index] = keywords[index]; // Use original casing
      }
    });

    setLockedInputs(newLocked);
    console.log("Updated locked inputs:", newLocked);
    
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

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen p-8">
        <h1 className="text-2xl font-bold mb-4">unprompted.</h1>
        {/* Media skeleton */}
        <div className="w-[300px] h-[300px] bg-gray-200 animate-pulse rounded-lg mb-8" />
        {/* Prompt skeleton */}
        <div className="w-full max-w-2xl space-y-3">
          <div className="h-4 bg-gray-200 animate-pulse rounded w-3/4" />
          <div className="h-4 bg-gray-200 animate-pulse rounded w-1/2" />
        </div>
        {/* Input skeleton */}
        <div className="flex gap-2 mt-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="w-24 h-10 bg-gray-200 animate-pulse rounded" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-8">
      <h1 className="text-2xl font-bold mb-4">unprompted.</h1>
      <MediaSection media={currentImage} isVideo={isVideo} />
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
            finalMedia={image}
            isVideo={isVideo}
          />
        )}
      </div>
    </div>
  );
};

export default GameLayout;