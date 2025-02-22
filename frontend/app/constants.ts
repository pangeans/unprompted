export const GAME_CONFIG = {
  MAX_ROUNDS: 5,
  COLORS: {
    RED: { r: 239, g: 68, b: 68 },     // Tailwind red-500
    YELLOW: { r: 245, g: 158, b: 11 },  // Tailwind yellow-500
    GREEN: { r: 34, g: 197, b: 94 },    // Tailwind green-500
  },
  SCORE_THRESHOLDS: {
    MIN: 0.0,
    MAX: 1.0,
    MID: 0.5
  }
} as const;

export const STYLE_CLASSES = {
  BUTTON: {
    PRIMARY: "bg-blue-500 text-white p-2 rounded hover:bg-blue-600",
  },
  INPUT: {
    CORRECT: "bg-green-500 text-white p-1 rounded font-bold",
    INCORRECT: "bg-red-500 text-white p-1 rounded font-bold",
    DEFAULT: "p-1 text-black w-auto focus:outline-none focus:ring-0 border-0 caret-black text-sm align-middle"
  }
} as const;