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
  speech_type: string[]; // Added speech_type to the interface
}

export const getRandomImageAndPrompt = async () => {
  const totalGames = 3; // assuming we have random-0 through random-4
  const randomIndex = Math.floor(Math.random() * totalGames);
  
  // Load the game data
  const response = await fetch(`/random-${randomIndex}.json`);
  const gameData: GameData = await response.json();
  
  // Load all similarity files
  const similarityPromises = gameData.similarity_files.map(file => 
    fetch(`${file}`).then(res => res.json())
  );
  const similarityData = await Promise.all(similarityPromises);
  
  // Create similarity dictionary where each keyword has its own mapping
  const similarityDict = gameData.keywords.reduce((acc: Record<string, Record<string, number>>, keyword, index) => {
    acc[keyword.toLowerCase()] = similarityData[index];
    return acc;
  }, {});

  return { 
    randomIndex, 
    image: gameData.image, 
    prompt: gameData.prompt, 
    keywords: gameData.keywords,
    similarityDict,
    speechTypes: gameData.speech_type // Include speech types in return value
  };
};