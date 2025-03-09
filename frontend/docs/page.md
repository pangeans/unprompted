# page.tsx Documentation

## Overview
`page.tsx` serves as the main entry point of the Unprompted application. It's a client-side component that manages the initial game state and data fetching.

## Line-by-Line Analysis

```typescript
'use client';
```
- Directive that marks this as a client-side component in Next.js

```typescript
import { useState, useEffect } from 'react';
```
- Imports React hooks for state management and side effects

```typescript
const [randomIndex, setRandomIndex] = useState<number>(0);
const [image, setRandomImage] = useState<string | null>(null);
const [prompt, setRandomPrompt] = useState('');
const [keywords, setRandomKeywords] = useState<string[]>([]);
const [similarityDict, setSimilarityDict] = useState<Record<string, Record<string, number>>>({});
```
- State declarations for core game data:
  - `randomIndex`: Tracks which game/image is currently active
  - `image`: Stores the URL of the current image
  - `prompt`: Stores the current game's prompt text
  - `keywords`: Array of target words players need to guess
  - `similarityDict`: Nested object storing similarity scores for word comparisons

```typescript
useEffect(() => {
  const loadGame = async () => {
    const { randomIndex, image, prompt, keywords, similarityDict } = await getRandomImageAndPrompt();
    setRandomIndex(randomIndex);
    setRandomImage(image);
    setRandomPrompt(prompt);
    setRandomKeywords(keywords);
    setSimilarityDict(similarityDict);
  };
  loadGame();
}, []);
```
- Effect hook that runs once on component mount
- Fetches initial game data asynchronously
- Updates all game-related state with fetched data

```typescript
return (
  <GameLayout 
    randomIndex={randomIndex} 
    image={image} 
    prompt={prompt} 
    keywords={keywords}
    similarityDict={similarityDict}
  />
);
```
- Renders the main GameLayout component
- Passes all game state as props

## Key Responsibilities
1. Initial game state management
2. Data fetching coordination
3. State distribution to game components