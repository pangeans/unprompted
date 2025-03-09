interface GameResponse {
  id: number;
  prompt_id: string;
  prompt_text: string;
  keywords: string[];
  image_url: string;
  similarity_data: Record<string, Record<string, number>>;
}

export const fetchLatestActiveGame = async (): Promise<GameResponse> => {
  const response = await fetch('/api/current-game');
  if (!response.ok) {
    throw new Error(`Error fetching game: ${response.statusText}`);
  }
  return await response.json();
};