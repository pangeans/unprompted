import { NextResponse } from 'next/server';
import { Pool } from 'pg';

export async function GET() {
  // Get database connection string from environment variable
  const DATABASE_URL = process.env.DATABASE_URL;
  
  if (!DATABASE_URL) {
    return NextResponse.json(
      { error: 'Database configuration missing' },
      { status: 500 }
    );
  }
  
  // Create a new PostgreSQL client
  const pgPool = new Pool({ connectionString: DATABASE_URL });
  
  try {
    // Query for the next scheduled game (with date_active greater than current time)
    const { rows } = await pgPool.query(`
      SELECT date_active
      FROM games
      WHERE date_active > NOW()
      ORDER BY date_active ASC
      LIMIT 1
    `);
    
    // If no future games are scheduled
    if (rows.length === 0) {
      return NextResponse.json({ nextGameTime: null });
    }
    
    // Return the date of the next scheduled game
    return NextResponse.json({ nextGameTime: rows[0].date_active });
  } catch (error) {
    console.error('Error fetching next game time:', error);
    return NextResponse.json(
      { error: 'Failed to fetch next game time' },
      { status: 500 }
    );
  } finally {
    // Close database connection
    await pgPool.end();
  }
}