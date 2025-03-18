# Game Limitation Feature Implementation

## Overview

This document explains how the "once per day" game limitation feature was implemented in the Unprompted frontend application.

## Requirements

1. Users should only be able to play the game once a day
2. After game completion, show:
   - Unblurred image/video
   - Filled-in prompt
   - Score squares
   - Timer to the next scheduled game (if any)
   - Message if no games are scheduled
3. Store and display the user's game results

## Implementation Approach

### 1. Cookie-Based Game Tracking with Result Storage

The implementation uses browser cookies to track when a user completes a game, including their performance details. Each game has a unique identifier based on its `prompt_id`, and a cookie is set when the game is completed.

Key functions in `utils.ts`:

```typescript
// Game result interface for storing in cookies
interface GameResult {
  completed: boolean;
  winningRound: number | null;
  guessSquares: string;  // Emoji representation of guesses
}

// Check if user has played today's game
export const hasPlayedToday = (gameId: string): GameResult | false => {
  if (typeof document === 'undefined') return false;
  const cookie = getCookie(`unprompted_played_${gameId}`);
  if (!cookie) return false;
  
  try {
    return JSON.parse(cookie);
  } catch {
    // For backward compatibility with old cookie format
    return { completed: true, winningRound: null, guessSquares: '' };
  }
};

// Mark a game as played and store results
export const markGameAsPlayed = (
  gameId: string, 
  winningRound: number | null, 
  guessHistory: { word: string; score: number }[][]
): void => {
  // Generate emoji squares for the guesses
  const guessSquares = guessHistory.map(round => 
    round.map(guess => {
      if (guess.score === 1) return "🟩";
      if (guess.score > 0 && guess.score < 1) return "🟨";
      return "⬛";
    }).join("")
  ).join("\n");

  // Create result object with game performance data
  const result: GameResult = {
    completed: true,
    winningRound,
    guessSquares
  };
  
  // Set cookie that expires at the end of the day (midnight)
  const now = new Date();
  const midnight = new Date(now);
  midnight.setHours(23, 59, 59, 999);
  
  setCookie(`unprompted_played_${gameId}`, JSON.stringify(result), {
    expires: midnight,
    path: '/'
  });
};
```

### 2. Next Game Timer API

A new API endpoint `/api/next-game-time` fetches the next scheduled game time from the PostgreSQL database. This endpoint:

1. Queries the database for games with `date_active` greater than current time
2. Returns the earliest scheduled game time, or `null` if no future games are scheduled

### 3. Game Completion UI

The `GameOverSection` component in `components.tsx` was enhanced to:
1. Display whether the user already played today
2. Show the original, unblurred image/video
3. Display the countdown timer to the next game
4. Show a message if no games are scheduled

### 4. Result Visualization

The `GuessHistorySection` component was updated to:
1. Display previous game results when loading a completed game
2. Render emoji squares (🟩, 🟨, ⬛) representing the user's performance
3. Show the full grid of attempts made in the previous session

### 5. GameLayout Integration

The main `GameLayout` component now:
1. Checks if the user has already played today's game on initial load
2. If already played, loads and displays previous game results
3. Shows the game in completed state with original image and solution
4. Uses the stored results for the "Copy Recap" functionality
5. Disables user input for completed games
6. Marks the game as played when it ends naturally

## Testing

To test the implementation:
1. Play a game to completion
2. The game should be marked as completed in cookies, with complete results
3. Refreshing the page should show the completed state with the original image and your previous results
4. The countdown to the next game should display (if scheduled)
5. The cookie should expire at midnight, allowing play again the next day

## Considerations

1. **Server-Side Validation**: Current implementation is client-side only using cookies. For a production application, consider adding server-side validation to prevent users from clearing cookies to play again.

2. **Time Zones**: Cookie expiration is set to midnight in the user's local time zone. Consider if this approach aligns with your game scheduling logic.

3. **Local Storage Alternative**: If longer persistence is desired, localStorage could be used instead of cookies, but the current approach ties the game completion to the daily cycle.

4. **User Accounts**: For more robust tracking, consider implementing user accounts in the future to track game completion server-side.