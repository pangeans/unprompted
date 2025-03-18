export const generateRecap = (randomIndex: number, guessHistory: { word: string; score: number }[][], round: number): string => {
  let recap = `unprompted ${randomIndex} ${round}/5\n`;
  guessHistory.forEach(guess => {
    recap += guess.map(r => {
      if (r.score === 1) return "🟩";
      if (r.score > 0 && r.score < 1) return "🟨";
      return "⬛";
    }).join("");
    if (guessHistory.indexOf(guess) < (guessHistory.length - 1)) {
      recap += "\n";
    };
  });
  return recap;
};

interface GameData {
  image: string;
  prompt: string;
  keywords: string[];
  similarity_files: string[];
  speech_type?: string[];
  pixelation_map?: Record<string, string> | null;  // Add pixelation_map to the interface
}

// Game result interface for storing in cookies
interface GameResult {
  completed: boolean;
  winningRound: number | null;
  guessSquares: string;  // Emoji representation of guesses
}

// Enhanced cookie handling utilities for game completion tracking
export const hasPlayedToday = (gameId: string): GameResult | false => {
  if (typeof document === 'undefined') return false;
  
  const cookie = getCookie(`unprompted_played_${gameId}`);
  if (!cookie) return false;
  
  try {
    return JSON.parse(cookie);
  } catch {
    // For backward compatibility with old cookie format
    return { completed: true, winningRound: null, guessSquares: '' };
  }
};

export const markGameAsPlayed = (
  gameId: string, 
  winningRound: number | null, 
  guessHistory: { word: string; score: number }[][]
): void => {
  if (typeof document === 'undefined') return;

  // Generate emoji squares for the guesses
  const guessSquares = guessHistory.map(round => 
    round.map(guess => {
      if (guess.score === 1) return "🟩";
      if (guess.score > 0 && guess.score < 1) return "🟨";
      return "⬛";
    }).join("")
  ).join("\n");

  // Create result object
  const result: GameResult = {
    completed: true,
    winningRound,
    guessSquares
  };

  // Set cookie that expires at the end of the day (midnight)
  const now = new Date();
  const midnight = new Date(now);
  midnight.setHours(23, 59, 59, 999);
  
  setCookie(`unprompted_played_${gameId}`, JSON.stringify(result), {
    expires: midnight,
    path: '/'
  });
};

export const getNextGameTime = async (): Promise<Date | null> => {
  try {
    const response = await fetch('/api/next-game-time');
    if (!response.ok) return null;
    
    const data = await response.json();
    return data.nextGameTime ? new Date(data.nextGameTime) : null;
  } catch (error) {
    console.error('Failed to fetch next game time:', error);
    return null;
  }
};

export const formatTimeRemaining = (targetDate: Date): string => {
  const now = new Date();
  const diffMs = targetDate.getTime() - now.getTime();
  
  if (diffMs <= 0) return "Available now";
  
  const diffSec = Math.floor(diffMs / 1000);
  const hours = Math.floor(diffSec / 3600);
  const minutes = Math.floor((diffSec % 3600) / 60);
  
  return `${hours}h ${minutes}m`;
};

// Helper functions for cookie management
const getCookie = (name: string): string | null => {
  if (typeof document === 'undefined') return null;
  
  const cookies = document.cookie.split(';');
  for (let i = 0; i < cookies.length; i++) {
    const cookie = cookies[i].trim();
    if (cookie.startsWith(name + '=')) {
      return cookie.substring(name.length + 1);
    }
  }
  return null;
};

interface CookieOptions {
  expires?: Date;
  path?: string;
  domain?: string;
  secure?: boolean;
  sameSite?: 'strict' | 'lax' | 'none';
}

const setCookie = (name: string, value: string, options: CookieOptions = {}): void => {
  if (typeof document === 'undefined') return;
  
  let cookieString = `${name}=${value}`;
  
  if (options.expires) cookieString += `; expires=${options.expires.toUTCString()}`;
  if (options.path) cookieString += `; path=${options.path}`;
  if (options.domain) cookieString += `; domain=${options.domain}`;
  if (options.secure) cookieString += '; secure';
  if (options.sameSite) cookieString += `; samesite=${options.sameSite}`;
  
  document.cookie = cookieString;
};

// Import the database API service
import { fetchLatestActiveGame } from './services/gameData';

export const getRandomImageAndPrompt = async () => {
  try {
    // Fetch game data from the database via API
    const gameData = await fetchLatestActiveGame();
    
    return { 
      // Use the prompt_id for randomIndex (used in share results)
      randomIndex: parseInt(gameData.prompt_id.replace(/[^0-9]/g, '')) || 0, 
      image: gameData.image_url, 
      prompt: gameData.prompt_text, 
      keywords: gameData.keywords,
      similarityDict: gameData.similarity_data,
      speechTypes: gameData.speech_types || [],
      pixelationMap: gameData.pixelation_map
    };
  } catch (error) {
    console.error('Failed to fetch game data:', error);
    
    // Fallback to local files if the API request fails
    const totalGames = 3;
    const randomIndex = Math.floor(Math.random() * totalGames);
    
    // Load the game data from local JSON
    const response = await fetch(`/random-${randomIndex}.json`);
    const localGameData: GameData = await response.json();
    
    // Load all similarity files
    const similarityPromises = localGameData.similarity_files.map(file => 
      fetch(`${file}`).then(res => res.json())
    );
    const similarityData = await Promise.all(similarityPromises);
    
    // Create similarity dictionary where each keyword has its own mapping
    const similarityDict = localGameData.keywords.reduce((acc: Record<string, Record<string, number>>, keyword, index) => {
      acc[keyword.toLowerCase()] = similarityData[index];
      return acc;
    }, {});
    
    return { 
      randomIndex, 
      image: localGameData.image, 
      prompt: localGameData.prompt, 
      keywords: localGameData.keywords,
      similarityDict,
      speechTypes: localGameData.speech_type || [],
      pixelationMap: localGameData.pixelation_map || null
    };
  }
};