import axios from 'axios';

// Define base API URL
export const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Helper function to build WebSocket URL
export const getWebSocketUrl = (path: string) => {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const wsBaseUrl = API_URL.replace(/^https?:\/\//, `${wsProtocol}://`);
  return `${wsBaseUrl}${path}`;
};

// Define API methods
export const gameApi = {
  // Create a new game
  createGame: async (smallBlind: number = 10, bigBlind: number = 20) => {
    try {
      const response = await api.post('/game/create', { smallBlind, bigBlind });
      return response.data;
    } catch (error) {
      console.error('Error creating game:', error);
      throw error;
    }
  },
  
  // Join a game
  joinGame: async (gameId: string, playerName: string, buyIn: number = 1000) => {
    try {
      const response = await api.post(`/game/join/${gameId}`, { playerName, buyIn });
      return response.data;
    } catch (error) {
      console.error('Error joining game:', error);
      throw error;
    }
  },
  
  // Start a game
  startGame: async (gameId: string) => {
    try {
      const response = await api.post(`/game/start/${gameId}`);
      return response.data;
    } catch (error) {
      console.error('Error starting game:', error);
      throw error;
    }
  },
  
  // Start next hand
  nextHand: async (gameId: string) => {
    try {
      const response = await api.post(`/game/next-hand/${gameId}`);
      return response.data;
    } catch (error) {
      console.error('Error starting next hand:', error);
      throw error;
    }
  },
  
  // Perform a player action
  performAction: async (gameId: string, playerId: string, action: string, amount?: number) => {
    try {
      const response = await api.post(`/game/action/${gameId}`, {
        player_id: playerId,
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
  },
  
  // Get WebSocket URL for a game
  getGameWebSocketUrl: (gameId: string, playerId?: string) => {
    return getWebSocketUrl(`/ws/game/${gameId}${playerId ? `?player_id=${playerId}` : ''}`);
  }
};

export default api;