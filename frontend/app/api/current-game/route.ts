import { NextResponse } from 'next/server';
import { Client as PostgresClient } from 'pg';
import { createClient as createRedisClient } from 'redis';

// Get all environment variables
const DATABASE_URL = process.env.DATABASE_URL;
const REDIS_URL = process.env.REDIS_URL;

export async function GET() {
  // Connect to PostgreSQL
  const pgClient = new PostgresClient({connectionString: DATABASE_URL});
  await pgClient.connect();
  // Connect to Redis
  const redisClient = createRedisClient({ url: REDIS_URL });
  await redisClient.connect();

  try {
    // Query for active games (games whose start time has passed)
    const { rows } = await pgClient.query(`
      SELECT id, prompt_id, prompt_text, keywords, speech_types, image_url, date_active
      FROM games
      WHERE date_active <= NOW()
      ORDER BY date_active DESC
      LIMIT 10
    `);

    // If no active games, return 404
    if (rows.length === 0) {
      return NextResponse.json(
        { error: 'No active games found' },
        { status: 404 }
      );
    }

    // If there are multiple games with the same most recent date, randomly choose one
    const latestGames = [rows[0]];
    for (let i = 1; i < rows.length; i++) {
      if (rows[i].date_active.getTime() === rows[0].date_active.getTime()) {
        latestGames.push(rows[i]);
      } else {
        break;
      }
    }

    // Randomly select one game if there are multiple games with the same date
    const selectedGame = latestGames[Math.floor(Math.random() * latestGames.length)];
    const { id, prompt_id, prompt_text, keywords, image_url } = selectedGame;
    
    // Parse keywords from JSON string if needed
    const parsedKeywords = typeof keywords === 'string' ? JSON.parse(keywords) : keywords;

    // Fetch similarity data for each keyword from Redis
    const similarityData: Record<string, Record<string, number>> = {};
    for (const keyword of parsedKeywords) {
      const keywordLower = keyword.toLowerCase();
      const similarityKey = `similarity:${keywordLower}`;
      const rawSimilarities = await redisClient.hGetAll(similarityKey);

      // Convert Redis string values to numbers
      const wordSimilarities: Record<string, number> = {};
      for (const [word, score] of Object.entries(rawSimilarities)) {
        wordSimilarities[word] = parseFloat(score);
      }

      if (Object.keys(wordSimilarities).length === 0) {
        throw new Error(`No similarity data found in Redis for keyword: ${keywordLower}`);
      }

      similarityData[keywordLower] = wordSimilarities;
    }

    return NextResponse.json({
      id,
      prompt_id,
      prompt_text,
      keywords: parsedKeywords,
      image_url,
      similarity_data: similarityData,
      speech_types: selectedGame.speech_types || []  // Add speech_types to response
    });
  } catch (error) {
    console.error('Error fetching game data:', error);
    return NextResponse.json(
      { error: 'Failed to fetch game data' },
      { status: 500 }
    );
  } finally {
    // Close database connections
    if (pgClient) await pgClient.end();
    if (redisClient) await redisClient.quit();
  }
}