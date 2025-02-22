import { useState, useEffect } from 'react';
import { getRandomImageAndPrompt } from '../utils';

export interface GameState {
  randomIndex: number;
  image: string | null;
  prompt: string;
  keywords: string[];
  isLoading: boolean;
  error: string | null;
}

export function useGameInitialization(): GameState {
  const [gameState, setGameState] = useState({
    randomIndex: 0,
    image: null as string | null,
    prompt: '',
    keywords: [] as string[]
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    try {
      const { randomIndex, image, prompt, keywords } = getRandomImageAndPrompt();
      setGameState({ randomIndex, image, prompt, keywords });
    } catch (err) {
      setError('Failed to initialize game data');
      console.error('Game initialization error:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return { ...gameState, isLoading, error };
}