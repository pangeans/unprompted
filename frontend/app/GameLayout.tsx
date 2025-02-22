'use client';
import { ImageSection } from "./components/ImageSection";
import { PromptSection } from "./components/PromptSection";
import { GuessHistorySection } from "./components/GuessHistorySection";
import { GameOverSection } from "./components/GameOverSection";
import { LoadingSpinner } from "./components/LoadingSpinner";
import { ErrorMessage } from "./components/ErrorMessage";
import { generateRecap } from "./utils";
import { useGameState } from "./hooks/useGameState";

interface GameLayoutProps {
  randomIndex: number;
  image: string | null;
  prompt: string;
  keywords: string[];
}

const GameLayout: React.FC<GameLayoutProps> = ({ randomIndex, image, prompt, keywords }) => {
  const {
    round,
    inputValues,
    lockedInputs,
    guessHistory,
    gameEnded,
    winningRound,
    isLoading,
    error,
    handleInputChange,
    handleSubmit
  } = useGameState(keywords);

  const copyToClipboard = () => {
    const recap = generateRecap(randomIndex, guessHistory, round);
    navigator.clipboard.writeText(recap);
  };

  if (error) {
    return <ErrorMessage message={error} />;
  }

  if (isLoading) {
    return <LoadingSpinner />;
  }

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
        <button 
          onClick={handleSubmit} 
          className="bg-blue-500 text-white p-2 rounded hover:bg-blue-600"
          disabled={isLoading}
        >
          Submit
        </button>
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