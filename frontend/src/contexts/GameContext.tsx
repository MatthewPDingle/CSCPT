import React, { createContext, useContext, useState, ReactNode } from 'react';

// Define types
export interface Card {
  rank: string;
  suit: string;
}

export interface Player {
  id: string;
  name: string;
  chips: number;
  position: number;
  cards: (string | null)[];
  isActive: boolean;
  isCurrent: boolean;
  isDealer: boolean;
}

export interface GameState {
  gameId: string;
  players: Player[];
  communityCards: (string | null)[];
  pot: number;
  currentBet: number;
  playerTurn: string;
  round: 'preflop' | 'flop' | 'turn' | 'river' | 'showdown';
}

interface GameContextType {
  gameState: GameState;
  isLoading: boolean;
  error: string | null;
  startGame: (numPlayers: number) => void;
  performAction: (action: string, amount?: number) => void;
}

// Initial game state
const initialGameState: GameState = {
  gameId: '',
  players: [],
  communityCards: [null, null, null, null, null],
  pot: 0,
  currentBet: 0,
  playerTurn: '',
  round: 'preflop'
};

// Create context
const GameContext = createContext<GameContextType | undefined>(undefined);

// Provider component
export const GameProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [gameState, setGameState] = useState<GameState>(initialGameState);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Mock function to start a game
  const startGame = async (numPlayers: number) => {
    setIsLoading(true);
    setError(null);
    
    try {
      // In a real implementation, this would call the backend API
      // For now, we'll simulate a response
      
      // Create mock players
      const mockPlayers: Player[] = [];
      
      // Add human player
      mockPlayers.push({
        id: 'player',
        name: 'You',
        chips: 1000,
        position: 0,
        cards: [null, null],
        isActive: true,
        isCurrent: false,
        isDealer: true
      });
      
      // Add AI players
      const aiNames = ['Bob', 'Alice', 'Charlie', 'Dave', 'Eve', 'Frank', 'Grace', 'Heidi'];
      
      for (let i = 0; i < numPlayers - 1; i++) {
        mockPlayers.push({
          id: `ai${i + 1}`,
          name: aiNames[i],
          chips: 1000 + Math.floor(Math.random() * 500),
          position: i + 1,
          cards: [null, null],
          isActive: true,
          isCurrent: i === 0, // First AI player's turn
          isDealer: false
        });
      }
      
      // Set game state
      setGameState({
        gameId: `game-${Date.now()}`,
        players: mockPlayers,
        communityCards: [null, null, null, null, null],
        pot: 0,
        currentBet: 0,
        playerTurn: 'ai1',
        round: 'preflop'
      });
      
    } catch (err) {
      setError('Failed to start game. Please try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  // Function to perform an action
  const performAction = async (action: string, amount?: number) => {
    setIsLoading(true);
    setError(null);
    
    try {
      // In a real implementation, this would call the backend API
      console.log(`Action: ${action}`, amount ? `Amount: ${amount}` : '');
      
      // For now, we'll just log the action and do nothing
      // In a real implementation, we would update the game state based on the response
      
    } catch (err) {
      setError('Failed to perform action. Please try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <GameContext.Provider
      value={{
        gameState,
        isLoading,
        error,
        startGame,
        performAction
      }}
    >
      {children}
    </GameContext.Provider>
  );
};

// Hook for using the game context
export const useGame = () => {
  const context = useContext(GameContext);
  if (context === undefined) {
    throw new Error('useGame must be used within a GameProvider');
  }
  return context;
};

export default GameContext;