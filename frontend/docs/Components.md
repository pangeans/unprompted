# Components Module

## Overview
This module contains the core game components that handle the visual and interactive elements of the game.

## ImageSection Component

### Props Interface
```typescript
interface ImageSectionProps {
  image: string | null;  // URL of the image to display
}
```

### Implementation Details
- Renders the game image using Next.js `Image` component
- Handles null image states
- Maintains consistent image dimensions (300x300)

## PromptSection Component

### Props Interface
```typescript
interface PromptSectionProps {
  originalPrompt: string;           // The full prompt text
  inputValues: string[];           // Current input values
  handleInputChange: Function;     // Input change handler
  keywords: string[];             // Target keywords
  gameEnded: boolean;            // Game state
  lockedInputs: boolean[];      // Locked input states
  invalidInputs?: boolean[];   // Invalid input states
  isAlternateLayout?: boolean; // Layout toggle
  guessHistory?: Array<Array<{word: string; score: number}>>; // Previous guesses
}
```

### Key Features
1. **Dynamic Input Rendering**: Replaces keywords in prompt with input fields
2. **Input Validation**: Visual feedback for invalid inputs
3. **Score Visualization**: Shows score history with color coding
4. **Layout Flexibility**: Supports both standard and alternate layouts
5. **Keyboard Navigation**: Tab and Enter key support

### State Management
- Tracks input focus states
- Manages input validation states
- Handles locked/completed inputs
- Maintains guess history display

### Scoring Visualization
```typescript
const interpolateColor = (score: number): string => {
  if (score === 1) return 'hsl(142, 76%, 36%)';      // Perfect match
  if (score >= 0.8) return `hsl(${120 * score}, 70%, 45%)`; // High similarity
  if (score >= 0.5) return `hsl(${120 * score}, 65%, 50%)`; // Medium similarity
  return `hsl(0, 75%, ${45 + score * 20}%)`;        // Low similarity
};
```

## GuessHistorySection Component

### Props Interface
```typescript
interface GuessHistorySectionProps {
  guessHistory: GuessHistoryItem[][];
  keywords: string[];
  isAlternateLayout?: boolean;
}
```

### Features
- Visual representation of past guesses
- Color-coded score feedback
- Progress tracking across rounds
- Alternate layout support

## GameOverSection Component

### Props Interface
```typescript
interface GameOverSectionProps {
  winningRound: number | null;
  copyToClipboard: () => void;
}
```

### Features
- Displays game completion message
- Shows winning round if applicable
- Provides sharing functionality

## CSS Classes and Styling
The components use a combination of Tailwind CSS classes and dynamic styling:

```typescript
const baseInputClasses = cn(
  "px-2 py-1 rounded-md text-sm min-w-fit",
  "transition-all duration-200 bg-transparent",
  {
    "bg-green-500 text-white font-bold": disabled && isLocked,
    "border-red-500 animate-shake": isInvalid,
    "empty:animate-pulse": isEmpty && !disabled,
    "ring-1 ring-muted/20": !disabled && !isInvalid,
    "w-full": isAlternateLayout
  }
);
```

## Event Handling
Components implement sophisticated event handling:
- Input focus management
- Keyboard navigation
- Copy to clipboard functionality
- Layout switching