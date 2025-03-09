# Unprompted Frontend Documentation

## Overview
Unprompted is a Next.js-based web application that implements a word-guessing game using AI-generated images. The application is built with TypeScript, React, and uses modern UI components from shadcn/ui.

## Core Files Structure
- `app/`
  - [`page.tsx`](./docs/page.md) - The main entry point of the application
  - [`GameLayout.tsx`](./docs/GameLayout.md) - The main game component that handles game state and layout
  - [`components.tsx`](./docs/components.md) - Reusable UI components for the game
  - [`utils.ts`](./docs/utils.md) - Utility functions for game logic

## Key Features
1. **Dynamic Game State Management**: Handles user inputs, scoring, and game progression
2. **Real-time Feedback**: Provides visual feedback for user guesses
3. **Responsive Design**: Supports both standard and alternate layouts
4. **Score Sharing**: Allows players to share their game results

## Technology Stack
- Next.js 13+
- React
- TypeScript
- Tailwind CSS
- shadcn/ui components

## Game Flow
1. Application loads with a random image and prompt
2. Players attempt to guess keywords in the prompt
3. Each guess is scored based on similarity to target words
4. Players have 5 rounds to guess all keywords correctly
5. Game ends when all words are guessed or rounds are exhausted

## Component Hierarchy
```
page.tsx
└── GameLayout.tsx
    ├── ImageSection
    ├── PromptSection
    ├── GuessHistorySection
    └── GameOverSection
```

For detailed documentation of each component, please refer to the individual component documentation linked above.