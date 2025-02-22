'use client';
import { useGameInitialization } from './hooks/useGameInitialization';
import GameLayout from './GameLayout';
import { LoadingSpinner } from './components/LoadingSpinner';
import { ErrorMessage } from './components/ErrorMessage';

export default function Home() {
  const { randomIndex, image, prompt, keywords, isLoading, error } = useGameInitialization();

  if (error) {
    return <ErrorMessage message={error} />;
  }

  if (isLoading) {
    return <LoadingSpinner />;
  }

  return (
    <GameLayout 
      randomIndex={randomIndex} 
      image={image} 
      prompt={prompt} 
      keywords={keywords}
    />
  );
}
