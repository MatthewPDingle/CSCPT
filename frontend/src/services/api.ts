import axios from 'axios';

// Define base API URL
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Define API methods
export const gameApi = {
  // Start a new game
  startGame: async (numPlayers: number) => {
    try {
      const response = await api.post('/game/start', { numPlayers });
      return response.data;
    } catch (error) {
      console.error('Error starting game:', error);
      throw error;
    }
  },
  
  // Perform a player action
  performAction: async (gameId: string, playerId: string, action: string, amount?: number) => {
    try {
      const response = await api.post('/game/action', {
        gameId,
        playerId,
        action,
        amount
      });
      return response.data;
    } catch (error) {
      console.error('Error performing action:', error);
      throw error;
    }
  },
  
  // Get game state
  getGameState: async (gameId: string) => {
    try {
      const response = await api.get(`/game/${gameId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching game state:', error);
      throw error;
    }
  }
};

export default api;