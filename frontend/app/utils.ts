export const checkWord = (word: string, targetWords: string[], position: number, round: number): string => {
  const lowerCaseWord = word.toLowerCase();
  const lowerCaseTargetWords = targetWords.map(target => target.toLowerCase());
  if (round <= 2) {
    if (lowerCaseTargetWords[position] === lowerCaseWord) return "green";
    if (lowerCaseTargetWords.includes(lowerCaseWord)) return "yellow";
    return "red";
  } else if (round <= 4) {
    if (lowerCaseTargetWords[position] === lowerCaseWord) return "green";
    if (lowerCaseTargetWords.includes(lowerCaseWord)) return "yellow";
    return "red";
  } else {
    if (lowerCaseTargetWords[position] === lowerCaseWord) return "green";
    if (lowerCaseTargetWords.includes(lowerCaseWord)) return "yellow";
    return "red";
  }
};

export const generateRecap = (randomIndex: number, guessHistory: { word: string; color: string }[][], round: number, winningRound: number | null): string => {
  let recap = `Unprompted ${randomIndex} ${round}/5\n`;
  guessHistory.forEach(guess => {
    recap += guess.map(r => {
      if (r.color === "green") return "🟩";
      if (r.color === "yellow") return "🟨";
      return "⬛";
    }).join("") + "\n";
  });
  if (winningRound !== null) {
    recap += `You won in round ${winningRound}!`;
  }
  else {
    recap += "You lose!";
  }
  return recap;
};

export const getRandomImageAndPrompt = () => {
  const images = [
    '/random-0.webp',    
    '/random-1.webp',    
    '/random-2.webp',    
    '/random-3.webp',    
    '/random-4.webp',    
  ];
  const prompts = [
    "Giant duck eating apples, realistic, detailed feathers, natural lighting, vibrant colors.",
    "Accountant doing taxes on the moon, comic book style, vintage colors, dramatic shading, space setting.",
    "Red dragon sleeping on a pile of NAND flash memory chips, realistic, detailed scales, high-tech theme, dramatic lighting.",
    "Santa Claus arm wrestling the Easter Bunny underwater, anime and manga style, static action, vibrant colors, clean lines.",
    "Very cute elephants playing poker in the jungle, Caravaggio style, dramatic lighting, rich textures, baroque realism.",
  ];
  const keywords = [
    ["Giant", "duck", "eating", "apples", "realistic"],
    ["Accountant", "taxes", "moon", "comic", "space"],
    ["dragon", "sleeping", "NAND", "flash", "memory"],
    ["Santa", "Claus", "Easter", "Bunny", "underwater"],
    ["elephants", "playing", "poker", "jungle", "Caravaggio"],
  ];
  const randomIndex = Math.floor(Math.random() * images.length);
  return { randomIndex: randomIndex, image: images[randomIndex], prompt: prompts[randomIndex], 
    keywords: keywords[randomIndex]};
};