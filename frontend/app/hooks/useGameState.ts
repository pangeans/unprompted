import { useState, useEffect } from 'react';
import { GameDataService } from '../services/gameData';

interface GuessResult {
  word: string;
  score: number;
}

interface GameState {
  round: number;
  inputValues: string[];
  lockedInputs: boolean[];
  guessHistory: GuessResult[][];
  gameEnded: boolean;
  winningRound: number | null;
  simMappings: { [key: string]: Record<string, number> };
  isLoading: boolean;
  error: string | null;
}

export function useGameState(keywords: string[]) {
  const [state, setState] = useState<GameState>({
    round: 1,
    inputValues: Array(keywords.length).fill(""),
    lockedInputs: Array(keywords.length).fill(false),
    guessHistory: [],
    gameEnded: false,
    winningRound: null,
    simMappings: {},
    isLoading: true,
    error: null
  });

  useEffect(() => {
    let mounted = true;

    const initializeGame = async () => {
      try {
        setState(prev => ({ ...prev, isLoading: true, error: null }));
        const mappings = await GameDataService.fetchSimMappings(keywords);
        
        if (mounted) {
          setState(prev => ({
            ...prev,
            simMappings: mappings,
            inputValues: Array(keywords.length).fill(""),
            lockedInputs: Array(keywords.length).fill(false),
            isLoading: false
          }));
        }
      } catch (error) {
        if (mounted) {
          setState(prev => ({
            ...prev,
            error: 'Failed to load game data',
            isLoading: false
          }));
        }
      }
    };

    initializeGame();
    return () => { mounted = false; };
  }, [keywords]);

  const handleInputChange = (index: number, value: string) => {
    if (state.isLoading || state.error) return;
    setState(prev => ({
      ...prev,
      inputValues: prev.inputValues.map((v, i) => i === index ? value : v)
    }));
  };

  const handleSubmit = () => {
    if (state.gameEnded || state.isLoading || state.error) return;

    setState(prev => {
      const result: GuessResult[] = [];
      const newLocked = [...prev.lockedInputs];
      const newInputValues = [...prev.inputValues];

      prev.inputValues.forEach((word, index) => {
        const mapping = prev.simMappings[keywords[index]];
        let score = 0;
        if (mapping && mapping[word.toLowerCase()] !== undefined) {
          score = mapping[word.toLowerCase()];
        }
        result.push({ word, score });
        
        if (word.toLowerCase() === keywords[index].toLowerCase()) {
          newLocked[index] = true;
          newInputValues[index] = keywords[index];
        }
      });

      const nextInputs = newLocked.map((locked, i) => 
        locked ? newInputValues[i] : "");
      
      const greenMatches = newLocked.filter(locked => locked).length;
      const isGameOver = prev.round >= 5 || greenMatches === keywords.length;
      const newWinningRound = greenMatches === keywords.length ? prev.round : null;

      return {
        ...prev,
        lockedInputs: newLocked,
        inputValues: nextInputs,
        guessHistory: [...prev.guessHistory, result],
        gameEnded: isGameOver,
        winningRound: isGameOver ? (newWinningRound ?? prev.winningRound) : null,
        round: isGameOver ? prev.round : prev.round + 1
      };
    });
  };

  return {
    ...state,
    handleInputChange,
    handleSubmit
  };
}