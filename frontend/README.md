# Unprompted Frontend

The frontend for the Unprompted game provides an interactive user interface where players can guess keywords used to generate AI images.

## Application Structure

```
frontend/
├── app/                    # Next.js app directory
│   ├── components.tsx      # Core game components
│   ├── GameLayout.tsx      # Main game layout component
│   ├── page.tsx            # Root page component
│   └── utils.ts            # Game utility functions
├── components/             # Shared UI components
│   └── ui/                 # shadcn/ui components
│       ├── badge.tsx       # Badge component
│       ├── button.tsx      # Button component
│       ├── card.tsx        # Card component
│       ├── dialog.tsx      # Dialog component
│       └── input.tsx       # Input component
└── lib/                    # Utility libraries
    └── utils.ts            # General utility functions
```

## Key Components

### Game Components

- **GameLayout**: The main game orchestration component that manages the game state and coordinates other components
- **ImageSection**: Displays the AI-generated image for the current prompt
- **PromptSection**: Shows the prompt text and input fields for guessing keywords
- **GuessHistorySection**: Shows the history of player guesses with visual feedback
- **GameOverSection**: Displays game results and provides sharing functionality

### UI Components

The application uses [shadcn/ui](https://ui.shadcn.com/) components for consistent styling:

- **Button**: Interactive button elements with various styles
- **Input**: Text input fields for player guesses
- **Card**: Container components for grouping related elements
- **Dialog**: Modal dialogs for important notifications and game completion
- **Badge**: Small status indicators for keywords and game state

## Game Flow

1. **Game Initialization**:
   - The game fetches a scheduled prompt from the backend
   - The AI-generated image and prompt text are loaded
   - Keywords and similarity data are prepared for player guessing

2. **Gameplay Rounds**:
   - Players progress through 5 rounds of increasing difficulty
   - Rounds 1-2: Basic keyword guessing
   - Rounds 3-4: Additional connector words appear
   - Round 5: Multiple choice options for final guesses

3. **Scoring**:
   - Words turn green when correctly guessed
   - Incorrect guesses receive feedback based on similarity scoring
   - Players can track their progress through visual feedback

4. **Game Completion**:
   - Players can view their final score and game statistics
   - Results can be shared in a Wordle-like format
   - Option to start a new game or view past games

## Technology Stack

- **Next.js**: React framework for server-side rendering and static generation
- **TypeScript**: Typed JavaScript for improved development experience
- **Tailwind CSS**: Utility-first CSS framework for responsive design
- **shadcn/ui**: Component library built on Radix UI primitives

## Development

### Setup

1. Install dependencies:
```bash
pnpm install
```

2. Run the development server:
```bash
pnpm dev
```

3. Open [http://localhost:3000](http://localhost:3000) to view the game

### Testing

Run tests with:
```bash
pnpm test
```

## Integration with Backend

The frontend integrates with the backend services through API endpoints:

- **/api/games**: Fetch available game data
- **/api/similarity**: Check word similarity for guesses
- **/api/sessions**: Track player sessions and performance

## Documentation

For more detailed documentation on specific components:

- [GameLayout Component](docs/GameLayout.md)
- [Components](docs/Components.md)
- [Page Component](docs/page.md)

## Contributing

1. Follow the project's coding standards (TypeScript, ESLint)
2. Write tests for new features
3. Submit pull requests with comprehensive descriptions
