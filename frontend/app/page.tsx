'use client';
import { useState, useEffect } from 'react';
import GameLayout from './GameLayout';
import { getRandomImageAndPrompt } from './utils';

export default function Home() {
  const [randomIndex, setRandomIndex] = useState<number>(0);
  const [image, setRandomImage] = useState<string | null>(null);
  const [prompt, setRandomPrompt] = useState('');
  const [keywords, setRandomKeywords] = useState<string[]>([]);

  useEffect(() => {
    const { randomIndex, image, prompt, keywords } = getRandomImageAndPrompt();
    setRandomIndex(randomIndex);
    setRandomImage(image);
    setRandomPrompt(prompt);
    setRandomKeywords(keywords);
  }, []);

  return (
    <GameLayout randomIndex={randomIndex} image={image} prompt={prompt} keywords={keywords}/>
  );
}
