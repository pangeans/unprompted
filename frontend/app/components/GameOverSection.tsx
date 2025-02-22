interface GameOverSectionProps {
  winningRound: number | null;
  copyToClipboard: () => void;
}

export const GameOverSection: React.FC<GameOverSectionProps> = ({ winningRound, copyToClipboard }) => (
  <div className="mt-4">
    <p className="text-xl font-bold">Game Over!</p>
    {winningRound !== null && <p>You won in round {winningRound}!</p>}
    <button 
      onClick={copyToClipboard} 
      className="bg-blue-500 text-white p-2 rounded hover:bg-blue-600 mt-2"
    >
      Copy Recap to Clipboard
    </button>
  </div>
);