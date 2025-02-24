# Unprompted Frontend Application Documentation

This document provides a comprehensive breakdown of the frontend application architecture and components.

## Application Structure

```
frontend/
├── app/                    # Next.js app directory
│   ├── components.tsx     # Core game components
│   ├── GameLayout.tsx    # Main game layout component
│   ├── page.tsx         # Root page component
│   └── utils.ts         # Game utility functions
├── components/           # Shared UI components
│   └── ui/             # shadcn/ui components
└── lib/                # Utility libraries
    └── utils.ts       # General utility functions
```

## Component Documentation

### Main Components
- [GameLayout Component](docs/GameLayout.md) - Main game orchestration component
- [Components](docs/Components.md) - Core game components (ImageSection, PromptSection, etc.)
- [Page Component](docs/Page.md) - Root page component

### Utilities
- [Game Utils](docs/GameUtils.md) - Game-specific utility functions 
- [Lib Utils](docs/LibUtils.md) - General utility functions

## Technology Stack

- **Framework**: Next.js
- **UI Components**: shadcn/ui
- **Styling**: Tailwind CSS
- **State Management**: React hooks

## Key Features

1. Image-based prompt guessing game
2. Interactive input fields with realtime feedback
3. Score tracking and game history
4. Alternate layout options
5. Copy results functionality

## Game Flow

1. Load random image and prompt
2. Player inputs guesses for keywords
3. Real-time validation and scoring
4. Progress tracking through 5 rounds
5. Game completion with sharable results
