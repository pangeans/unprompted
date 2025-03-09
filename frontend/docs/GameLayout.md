# GameLayout.tsx Documentation

## Overview
`GameLayout.tsx` is the primary game component that manages the game state, user interactions, and layout rendering. It implements the core game logic and coordinates between various sub-components.

## Line-by-Line Analysis

```typescript
'use client';
```
- Marks component as client-side rendered

```typescript
interface GameLayoutProps {
  randomIndex: number;
  image: string | null;
  prompt: string;
  keywords: string[];
  similarityDict: Record<string, Record<string, number>>;
}
```
- Defines the component's props interface
- `similarityDict` contains word similarity scores for evaluating guesses

```typescript
const [round, setRound] = useState(1);
const [inputValues, setInputValues] = useState<string[]>(Array(keywords.length).fill(""));
const [lockedInputs, setLockedInputs] = useState<boolean[]>(Array(keywords.length).fill(false));
const [invalidInputs, setInvalidInputs] = useState<boolean[]>(Array(keywords.length).fill(false));
const [guessHistory, setGuessHistory] = useState<{ word: string; score: number }[][]>([]);
const [gameEnded, setGameEnded] = useState(false);
const [winningRound, setWinningRound] = useState<number | null>(null);
const [isAlternateLayout, setIsAlternateLayout] = useState(false);
```
- State management for:
  - Current game round (max 5)
  - Player input values
  - Locked (correctly guessed) inputs
  - Invalid input indicators
  - History of all guesses and scores
  - Game state flags
  - Layout preference

```typescript
useEffect(() => {
  setInputValues(Array(keywords.length).fill(""));
  setLockedInputs(Array(keywords.length).fill(false));
  setInvalidInputs(Array(keywords.length).fill(false));
}, [keywords]);
```
- Resets game state when keywords change
- Ensures clean state for new games

```typescript
const handleInputChange = (index: number, value: string) => {
  const newInputValues = [...inputValues];
  newInputValues[index] = value;
  setInputValues(newInputValues);
  if (invalidInputs[index]) {
    const newInvalidInputs = [...invalidInputs];
    newInvalidInputs[index] = false;
    setInvalidInputs(newInvalidInputs);
  }
};
```
- Handles user input changes
- Updates input values
- Clears invalid state on new input

```typescript
const handleSubmit = () => {
  // Validation checks
  if (gameEnded) return;
  const emptyFields = inputValues.map((value, index) => 
    !value.trim() && !lockedInputs[index]
  );
  
  if (emptyFields.some(isEmpty => isEmpty)) {
    setInvalidInputs(emptyFields);
    return;
  }

  // Process guesses and update game state
  const result = [];
  const newLocked = [...lockedInputs];
  const newInputValues = [...inputValues];

  // Score calculation and input locking
  inputValues.forEach((word, index) => {
    let score = 0;
    const keyword = keywords[index].toLowerCase();
    const wordLower = word.toLowerCase();
    
    if (similarityDict[keyword] && similarityDict[keyword][wordLower] !== undefined) {
      score = similarityDict[keyword][wordLower];
    }
    result.push({ word, score });
    
    if (wordLower === keyword) {
      newLocked[index] = true;
      newInputValues[index] = keywords[index];
    }
  });

  // Update game state
  setLockedInputs(newLocked);
  setInputValues(newLocked.map((locked, i) => locked ? newInputValues[i] : ""));
  setInvalidInputs(Array(keywords.length).fill(false));
  setGuessHistory(prev => [...prev, result]);

  // Check game end conditions
  const greenMatches = newLocked.filter(locked => locked).length;
  if (round >= 5 || greenMatches === keywords.length) {
    setGameEnded(true);
    if (greenMatches === keywords.length) {
      setWinningRound(round);
    }
  } else {
    setRound(prev => prev + 1);
  }
};
```
- Core game logic implementation
- Processes user guesses
- Updates game state
- Handles win/lose conditions

## Key Features
1. **Input Management**
   - Tracks multiple input fields
   - Validates user input
   - Provides visual feedback

2. **Game State Control**
   - Manages round progression
   - Tracks correct guesses
   - Handles game completion

3. **Layout Flexibility**
   - Supports standard and alternate layouts
   - Responsive design

4. **Score Tracking**
   - Records guess history
   - Calculates similarity scores
   - Shows visual feedback

## Component Structure
```
GameLayout
├── Header + Layout Toggle
├── ImageSection
├── PromptSection
├── Submit Button
└── Results Section
    ├── Round Counter
    ├── GuessHistorySection
    └── GameOverSection (conditional)
```