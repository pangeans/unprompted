export const keywords = ["Jesus", "teaching", "superhero", "taxes", "comic"];
export const connectorWords = ["in", "a", "with", "and", "the", "background"];
export const originalPrompt = "Jesus teaching superhero how to do taxes, comic book style, vintage colors, dramatic shading, classic panels.";

export const checkWord = (word: string, targetWords: string[], position: number, round: number): string => {
  if (round <= 2) {
    if (targetWords[position] === word) return "green";
    if (targetWords.includes(word)) return "yellow";
    return "red";
  } else if (round <= 4) {
    if (connectorWords.includes(word)) return "gray";
    if (targetWords[position] === word) return "green";
    if (targetWords.includes(word)) return "yellow";
    return "red";
  } else {
    if (targetWords[position] === word) return "green";
    if (targetWords.includes(word)) return "yellow";
    return "red";
  }
};

export const generateRecap = (guessHistory: { word: string; color: string }[][], round: number, winningRound: number | null): string => {
  let recap = `Unprompted 1 ${round}/5\n`;
  guessHistory.forEach(guess => {
    recap += guess.map(r => {
      if (r.color === "green") return "🟩";
      if (r.color === "yellow") return "🟨";
      return "⬛";
    }).join("") + "\n";
  });
  if (winningRound !== null) {
    recap += `You won in round ${winningRound}!\n`;
  }
  return recap;
};