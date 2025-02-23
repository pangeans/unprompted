# unprompted Frontend

The frontend web application for the unprompted game, built with Next.js 15, React 19, and TailwindCSS.

## Features

- Real-time word similarity matching
- Responsive design with shadcn/ui components
- Dark mode support
- Shareable game results
- Progressive game mechanics across 5 rounds

## Tech Stack

- Next.js 15 with App Router
- React 19
- TailwindCSS for styling
- shadcn/ui for UI components
- Vercel Analytics

## Getting Started

1. Install dependencies:
```bash
pnpm install
```

2. Run the development server:
```bash
pnpm dev
```

3. Open [http://localhost:3000](http://localhost:3000) to play the game

## Project Structure

```
frontend/
├── app/                # Next.js app router
│   ├── components.tsx  # Game components
│   ├── GameLayout.tsx # Main game logic
│   ├── page.tsx       # Entry point
│   └── utils.ts       # Helper functions
├── components/        # Reusable UI components
├── lib/              # Utility functions
└── public/           # Static files and game data
```

## Game Mechanics

The game uses semantic similarity to match player guesses with target keywords. Each guess is evaluated against pre-computed embeddings to determine how close it is to the correct answer.

- Green highlights indicate exact matches
- Color gradients show how close a guess is to the target word
- Input fields lock when correct words are guessed

## Deployment

The app is optimized for deployment on Vercel. Simply push to your repository and connect it to Vercel for automatic deployments.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request
