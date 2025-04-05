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

// Types for cash game API
export interface CashGameOptions {
  name?: string;
  minBuyIn?: number;
  maxBuyIn?: number;
  smallBlind?: number;
  bigBlind?: number;
  ante?: number;
  tableSize?: number;
  bettingStructure?: 'no_limit' | 'pot_limit' | 'fixed_limit';
  rakePercentage?: number;
  rakeCap?: number;
}

// Types for game setup API
export interface PlayerSetupInput {
  name: string;
  is_human: boolean;
  archetype?: string;
  position?: number;
  buy_in: number;
}

export interface GameSetupInput {
  game_mode: 'cash' | 'tournament';
  small_blind?: number;
  big_blind?: number;
  ante?: number;
  min_buy_in?: number;
  max_buy_in?: number;
  table_size?: number;
  betting_structure?: string;
  rake_percentage?: number;
  rake_cap?: number;
  tier?: string;
  stage?: string;
  buy_in_amount?: number;
  starting_chips?: number;
  players: PlayerSetupInput[];
}

// Define API methods
export const gameApi = {
  // Setup a complete game from the lobby
  setupGame: async (gameSetup: GameSetupInput) => {
    try {
      const response = await api.post('/setup/game', gameSetup);
      return response.data;
    } catch (error) {
      console.error('Error setting up game:', error);
      throw error;
    }
  },
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
  
  // Create a cash game with custom options
  createCashGame: async (options: CashGameOptions) => {
    try {
      const response = await api.post('/cash-games/', options);
      return response.data;
    } catch (error) {
      console.error('Error creating cash game:', error);
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
  },

  // Cash game player management methods
  cashGame: {
    // Add a player to a cash game
    addPlayer: async (gameId: string, playerName: string, buyIn: number, options?: {
      isHuman?: boolean,
      archetype?: string,
      position?: number
    }) => {
      try {
        const response = await api.post(`/cash-games/${gameId}/players`, {
          name: playerName,
          buy_in: buyIn,
          is_human: options?.isHuman ?? false,
          archetype: options?.archetype,
          position: options?.position
        });
        return response.data;
      } catch (error) {
        console.error('Error adding player to cash game:', error);
        throw error;
      }
    },

    // Cash out a player
    cashOutPlayer: async (gameId: string, playerId: string) => {
      try {
        const response = await api.post(`/cash-games/${gameId}/players/${playerId}/cashout`);
        return response.data;
      } catch (error) {
        console.error('Error cashing out player:', error);
        throw error;
      }
    },

    // Rebuy for a player
    rebuyPlayer: async (gameId: string, playerId: string, amount: number) => {
      try {
        const response = await api.post(`/cash-games/${gameId}/players/${playerId}/rebuy`, { amount });
        return response.data;
      } catch (error) {
        console.error('Error performing rebuy:', error);
        throw error;
      }
    },

    // Top up player to maximum buy-in
    topUpPlayer: async (gameId: string, playerId: string) => {
      try {
        const response = await api.post(`/cash-games/${gameId}/players/${playerId}/topup`);
        return response.data;
      } catch (error) {
        console.error('Error topping up player:', error);
        throw error;
      }
    }
  }
};

export default api;