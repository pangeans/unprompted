'use client';
import { useState, useEffect } from 'react';
import GameLayout from './GameLayout';
import { fetchLatestActiveGame } from './services/gameData';

export default function Home() {
  const [randomIndex, setRandomIndex] = useState<number>(0);
  const [image, setRandomImage] = useState<string | null>(null);
  const [prompt, setRandomPrompt] = useState('');
  const [keywords, setRandomKeywords] = useState<string[]>([]);
  const [similarityDict, setSimilarityDict] = useState<Record<string, Record<string, number>>>({});
  const [speechTypes, setSpeechTypes] = useState<string[]>([]);

  useEffect(() => {
    const loadGame = async () => {
      const { 
        prompt_id, 
        image_url, 
        prompt_text, 
        keywords, 
        similarity_data,
        speech_types 
      } = await fetchLatestActiveGame();

      setRandomIndex(parseInt(prompt_id.replace(/[^0-9]/g, '')) || 0);
      setRandomImage(image_url);
      setRandomPrompt(prompt_text);
      setRandomKeywords(keywords);
      setSimilarityDict(similarity_data);
      setSpeechTypes(speech_types || []);
    };
    loadGame();
  }, []);

  return (
    <GameLayout 
      randomIndex={randomIndex} 
      image={image} 
      prompt={prompt} 
      keywords={keywords}
      similarityDict={similarityDict}
      speechTypes={speechTypes}
    />
  );
}
