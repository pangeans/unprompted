export interface SimMapping {
  [key: string]: Record<string, number>;
}

export class GameDataError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'GameDataError';
  }
}

export class GameDataService {
  private static async fetchSingleMapping(keyword: string): Promise<Record<string, number>> {
    try {
      const res = await fetch(`/${keyword.toLowerCase()}.json`);
      if (!res.ok) {
        throw new GameDataError(`HTTP error! status: ${res.status}`);
      }
      const data = await res.json();
      
      // Validate the response structure
      if (typeof data !== 'object' || data === null) {
        throw new GameDataError(`Invalid mapping data for keyword: ${keyword}`);
      }
      
      // Validate each entry in the mapping
      Object.entries(data).forEach(([key, value]) => {
        if (typeof value !== 'number' || value < 0 || value > 1) {
          throw new GameDataError(`Invalid score value for word "${key}" in keyword "${keyword}"`);
        }
      });

      return data;
    } catch (err) {
      if (err instanceof GameDataError) {
        throw err;
      }
      throw new GameDataError(`Failed to load mapping for ${keyword}: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  }

  static async fetchSimMappings(keywords: string[]): Promise<SimMapping> {
    if (!Array.isArray(keywords) || keywords.length === 0) {
      throw new GameDataError('Invalid or empty keywords array');
    }

    const mappings: SimMapping = {};
    try {
      await Promise.all(
        keywords.map(async (keyword) => {
          if (typeof keyword !== 'string' || !keyword) {
            throw new GameDataError('Invalid keyword provided');
          }
          try {
            mappings[keyword] = await this.fetchSingleMapping(keyword);
          } catch (err) {
            console.error(`Error loading mapping for ${keyword}:`, err);
            // Instead of silently failing, we store an empty mapping
            mappings[keyword] = {};
          }
        })
      );
    } catch (err) {
      throw new GameDataError(`Failed to fetch mappings: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }

    return mappings;
  }
}