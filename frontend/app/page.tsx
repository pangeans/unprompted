'use client';
import { useState, useEffect } from 'react';
import GameLayout from './GameLayout';
import { getRandomImageAndPrompt } from './utils';

export default function Home() {
  const [randomIndex, setRandomIndex] = useState<number>(0);
  const [image, setRandomImage] = useState<string | null>(null);
  const [originalImage, setOriginalImage] = useState<string>('');
  const [blurPatternBase, setBlurPatternBase] = useState<string>('');
  const [prompt, setRandomPrompt] = useState('');
  const [keywords, setRandomKeywords] = useState<string[]>([]);
  const [similarityDict, setSimilarityDict] = useState<Record<string, Record<string, number>>>({});
  const [speechTypes, setSpeechTypes] = useState<string[]>([]);

  useEffect(() => {
    const loadGame = async () => {
      const { 
        randomIndex, 
        image, 
        originalImage, 
        blurPatternBase,
        prompt, 
        keywords, 
        similarityDict, 
        speechTypes 
      } = await getRandomImageAndPrompt();
      
      setRandomIndex(randomIndex);
      setRandomImage(image);
      setOriginalImage(originalImage);
      setBlurPatternBase(blurPatternBase);
      setRandomPrompt(prompt);
      setRandomKeywords(keywords);
      setSimilarityDict(similarityDict);
      setSpeechTypes(speechTypes || []);
    };
    loadGame();
  }, []);

  return (
    <GameLayout 
      randomIndex={randomIndex} 
      image={image} 
      originalImage={originalImage}
      blurPatternBase={blurPatternBase}
      prompt={prompt} 
      keywords={keywords}
      similarityDict={similarityDict}
      speechTypes={speechTypes}
    />
  );
}
