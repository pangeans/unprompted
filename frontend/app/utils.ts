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
  speech_type: string[];
}

export const getRandomImageAndPrompt = async () => {
  const totalGames = 3; // assuming we have random-0 through random-2
  const randomIndex = Math.floor(Math.random() * totalGames);
  
  // Load the game data from the new folder structure
  const response = await fetch(`/random-${randomIndex}/game_config.json`);
  const gameData: GameData = await response.json();
  
  // Path for original unblurred image (to show at the end)
  const originalImagePath = `/random-${randomIndex}/original_image.webp`;
  
  // Path for fully blurred image (starting point)
  const blurredImagePath = `/random-${randomIndex}/blurred_images/0blur_1blur_2blur_3blur_4blur.webp`;
  
  // Path pattern for partially blurred images (will be constructed dynamically based on guessed keywords)
  const blurPatternBase = `/random-${randomIndex}/blurred_images/`;
  
  // Load all similarity files from the new path structure
  const similarityPromises = gameData.similarity_files.map(file => {
    // Handle both absolute and relative paths
    const filePath = file.startsWith('/')
      ? `/random-${randomIndex}${file}` // Prefix with random-N folder
      : `/random-${randomIndex}/${file}`;
    return fetch(filePath).then(res => res.json());
  });
  
  const similarityData = await Promise.all(similarityPromises);
  
  // Create similarity dictionary where each keyword has its own mapping
  const similarityDict = gameData.keywords.reduce((acc: Record<string, Record<string, number>>, keyword, index) => {
    acc[keyword.toLowerCase()] = similarityData[index];
    return acc;
  }, {});

  return { 
    randomIndex, 
    image: blurredImagePath, // Start with fully blurred image
    originalImage: originalImagePath, // Original unblurred image for game over
    blurPatternBase, // Base path for constructing partial blur images
    prompt: gameData.prompt, 
    keywords: gameData.keywords,
    similarityDict,
    speechTypes: gameData.speech_type
  };
};