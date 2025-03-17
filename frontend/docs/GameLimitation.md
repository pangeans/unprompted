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

## Implementation Approach

### 1. Cookie-Based Game Tracking

The implementation uses browser cookies to track when a user completes a game. Each game has a unique identifier based on its `prompt_id`, and a cookie is set when the game is completed.

Key functions in `utils.ts`:

```typescript
// Check if user has played today's game
export const hasPlayedToday = (gameId: string): boolean => {
  if (typeof document === 'undefined') return false;
  const cookie = getCookie(`unprompted_played_${gameId}`);
  return !!cookie;
};

// Mark a game as played
export const markGameAsPlayed = (gameId: string): void => {
  // Set cookie that expires at the end of the day (midnight)
  const now = new Date();
  const midnight = new Date(now);
  midnight.setHours(23, 59, 59, 999);
  
  setCookie(`unprompted_played_${gameId}`, 'true', {
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

```typescript
// Inside GameOverSection component
const [nextGameTime, setNextGameTime] = useState<Date | null>(null);
const [timeRemaining, setTimeRemaining] = useState<string>('');

useEffect(() => {
  const fetchNextGame = async () => {
    const time = await getNextGameTime();
    setNextGameTime(time);
    
    if (time) {
      setTimeRemaining(formatTimeRemaining(time));
    }
  };
  
  fetchNextGame();
  
  // Update the countdown every minute
  const intervalId = setInterval(() => {
    if (nextGameTime) {
      setTimeRemaining(formatTimeRemaining(nextGameTime));
    }
  }, 60000);
  
  return () => clearInterval(intervalId);
}, []);
```

### 4. GameLayout Integration

The main `GameLayout` component now:
1. Checks if the user has already played today's game on initial load
2. If already played, shows the game in completed state with original image and solution
3. Disables user input for completed games
4. Marks the game as played when it ends naturally

```typescript
// Check if user has already played
useEffect(() => {
  if (randomIndex && !isLoading) {
    const gameId = `game-${randomIndex}`;
    const played = hasPlayedToday(gameId);
    setAlreadyPlayed(played);
    
    if (played) {
      setGameEnded(true);
      setCurrentImage(image);
    }
  }
}, [randomIndex, isLoading, image]);
```

## Testing

To test the implementation:
1. Play a game to completion
2. The game should be marked as completed in cookies
3. Refreshing the page should show the completed state with the original image
4. The countdown to the next game should display (if scheduled)
5. The cookie should expire at midnight, allowing play again the next day

## Considerations

1. **Server-Side Validation**: Current implementation is client-side only using cookies. For a production application, consider adding server-side validation to prevent users from clearing cookies to play again.

2. **Time Zones**: Cookie expiration is set to midnight in the user's local time zone. Consider if this approach aligns with your game scheduling logic.

3. **Local Storage Alternative**: If longer persistence is desired, localStorage could be used instead of cookies, but the current approach ties the game completion to the daily cycle.

4. **User Accounts**: For more robust tracking, consider implementing user accounts in the future to track game completion server-side.