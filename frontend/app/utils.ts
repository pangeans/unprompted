export const generateRecap = (randomIndex: number, guessHistory: { word: string; score: number }[][], round: number): string => {
  let recap = `Unprompted ${randomIndex} ${round}/5\n`;
  guessHistory.forEach(guess => {
    recap += guess.map(r => {
      if (r.score === 1) return "🟩";
      if (r.score > 0 && r.score < 1) return "🟨";
      return "⬛";
    }).join("") + "\n";
  });
  return recap;
};

interface GameData {
  image: string;
  prompt: string;
  keywords: string[];
  similarity_files: string[];
  speech_type?: string[]; // Added speech_type to the interface
}

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
      speechTypes: [] // This field is optional and might not be in the database yet
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
      speechTypes: localGameData.speech_type || []
    };
  }
};