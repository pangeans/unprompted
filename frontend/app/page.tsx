'use client';
import { useState, useEffect } from 'react';
import GameLayout from './GameLayout';
import { getRandomImageAndPrompt } from './utils';

export default function Home() {
  const [image, setRandomImage] = useState<string | null>(null);
  const [prompt, setRandomPrompt] = useState('');
  const [keywords, setRandomKeywords] = useState<string[]>([]);

  useEffect(() => {
    const { image, prompt, keywords } = getRandomImageAndPrompt();
    setRandomImage(image);
    setRandomPrompt(prompt);
    setRandomKeywords(keywords);
  }, []);

  return (
    <GameLayout image={image} prompt={prompt} keywords={keywords}/>
  );
}
