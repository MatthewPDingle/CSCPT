import { renderHook, act } from '@testing-library/react';
import { useGameWebSocket } from './useGameWebSocket';
import { useWebSocket } from './useWebSocket';

// Mock the useWebSocket hook
jest.mock('./useWebSocket', () => ({
  useWebSocket: jest.fn()
}));

describe('useGameWebSocket', () => {
  // Setup default mock implementation for useWebSocket
  const mockSendMessage = jest.fn();
  const mockStatus = 'open';
  const mockLastMessage = null;
  const mockReconnect = jest.fn();
  
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Set up default return values for useWebSocket
    (useWebSocket as jest.Mock).mockReturnValue({
      sendMessage: mockSendMessage,
      lastMessage: mockLastMessage,
      status: mockStatus,
      reconnect: mockReconnect
    });
  });
  
  it('should construct correct WebSocket URL', () => {
    renderHook(() => useGameWebSocket('game123', 'player456'));
    
    // Check that useWebSocket was called with correct URL
    const wsUrl = (useWebSocket as jest.Mock).mock.calls[0][0];
    expect(wsUrl).toContain('/ws/game/game123');
    expect(wsUrl).toContain('player_id=player456');
  });
  
  it('should allow observer mode (no player ID)', () => {
    renderHook(() => useGameWebSocket('game123'));
    
    // Check that useWebSocket was called with URL without player_id
    const wsUrl = (useWebSocket as jest.Mock).mock.calls[0][0];
    expect(wsUrl).toContain('/ws/game/game123');
    expect(wsUrl).not.toContain('player_id=');
  });
  
  it('should parse game state messages', () => {
    const { result } = renderHook(() => useGameWebSocket('game123', 'player456'));
    
    // Mock receiving a game state message
    const gameStateMessage = {
      data: JSON.stringify({
        type: 'game_state',
        data: {
          game_id: 'game123',
          players: [],
          community_cards: [],
          pots: [],
          total_pot: 0,
          current_round: 'PREFLOP',
          button_position: 0,
          current_player_idx: 0,
          current_bet: 0,
          small_blind: 10,
          big_blind: 20
        }
      })
    };
    
    // Get the onMessage handler
    const onMessageHandler = (useWebSocket as jest.Mock).mock.calls[0][1].onMessage;
    
    // Call the handler with the game state message
    act(() => {
      onMessageHandler(gameStateMessage);
    });
    
    // Check that the game state was updated
    expect(result.current.gameState).not.toBeNull();
    expect(result.current.gameState?.game_id).toBe('game123');
  });
  
  it('should parse player action messages', () => {
    const { result } = renderHook(() => useGameWebSocket('game123', 'player456'));
    
    // Mock receiving a player action message
    const actionMessage = {
      data: JSON.stringify({
        type: 'player_action',
        data: {
          player_id: 'player789',
          action: 'FOLD',
          timestamp: '2023-01-01T00:00:00Z'
        }
      })
    };
    
    // Get the onMessage handler
    const onMessageHandler = (useWebSocket as jest.Mock).mock.calls[0][1].onMessage;
    
    // Call the handler with the action message
    act(() => {
      onMessageHandler(actionMessage);
    });
    
    // Check that the last action was updated
    expect(result.current.lastAction).not.toBeNull();
    expect(result.current.lastAction?.player_id).toBe('player789');
    expect(result.current.lastAction?.action).toBe('FOLD');
  });
  
  it('should parse action request messages', () => {
    const { result } = renderHook(() => useGameWebSocket('game123', 'player456'));
    
    // Mock receiving an action request message
    const requestMessage = {
      data: JSON.stringify({
        type: 'action_request',
        data: {
          handId: 'hand123',
          player_id: 'player456',
          options: ['FOLD', 'CHECK', 'BET'],
          callAmount: 0,
          minRaise: 20,
          maxRaise: 1000,
          timeLimit: 30,
          timestamp: '2023-01-01T00:00:00Z'
        }
      })
    };
    
    // Get the onMessage handler
    const onMessageHandler = (useWebSocket as jest.Mock).mock.calls[0][1].onMessage;
    
    // Call the handler with the request message
    act(() => {
      onMessageHandler(requestMessage);
    });
    
    // Check that the action request was updated
    expect(result.current.actionRequest).not.toBeNull();
    expect(result.current.actionRequest?.player_id).toBe('player456');
    expect(result.current.actionRequest?.options).toContain('FOLD');
  });
  
  it('should parse hand result messages', () => {
    const { result } = renderHook(() => useGameWebSocket('game123', 'player456'));
    
    // Mock receiving a hand result message
    const resultMessage = {
      data: JSON.stringify({
        type: 'hand_result',
        data: {
          handId: 'hand123',
          winners: [
            {
              player_id: 'player789',
              name: 'Player 789',
              amount: 100
            }
          ],
          players: [],
          board: ['As', 'Ks', 'Qs', 'Js', 'Ts'],
          timestamp: '2023-01-01T00:00:00Z'
        }
      })
    };
    
    // Get the onMessage handler
    const onMessageHandler = (useWebSocket as jest.Mock).mock.calls[0][1].onMessage;
    
    // Call the handler with the result message
    act(() => {
      onMessageHandler(resultMessage);
    });
    
    // Check that the hand result was updated
    expect(result.current.handResult).not.toBeNull();
    expect(result.current.handResult?.handId).toBe('hand123');
    expect(result.current.handResult?.winners[0].player_id).toBe('player789');
  });
  
  it('should parse chat messages', () => {
    const { result } = renderHook(() => useGameWebSocket('game123', 'player456'));
    
    // Mock receiving a chat message
    const chatMessage = {
      data: JSON.stringify({
        type: 'chat',
        data: {
          from: 'Player 789',
          text: 'Hello, world!',
          timestamp: '2023-01-01T00:00:00Z'
        }
      })
    };
    
    // Get the onMessage handler
    const onMessageHandler = (useWebSocket as jest.Mock).mock.calls[0][1].onMessage;
    
    // Call the handler with the chat message
    act(() => {
      onMessageHandler(chatMessage);
    });
    
    // Check that the chat messages were updated
    expect(result.current.chatMessages.length).toBe(1);
    expect(result.current.chatMessages[0].from).toBe('Player 789');
    expect(result.current.chatMessages[0].text).toBe('Hello, world!');
  });
  
  it('should parse error messages', () => {
    const { result } = renderHook(() => useGameWebSocket('game123', 'player456'));
    
    // Mock receiving an error message
    const errorMessage = {
      data: JSON.stringify({
        type: 'error',
        data: {
          code: 'invalid_action',
          message: 'Invalid action',
          detail: 'Fold is not allowed'
        }
      })
    };
    
    // Get the onMessage handler
    const onMessageHandler = (useWebSocket as jest.Mock).mock.calls[0][1].onMessage;
    
    // Call the handler with the error message
    act(() => {
      onMessageHandler(errorMessage);
    });
    
    // Check that the errors were updated
    expect(result.current.errors.length).toBe(1);
    expect(result.current.errors[0].code).toBe('invalid_action');
    expect(result.current.errors[0].message).toBe('Invalid action');
  });
  
  it('should send player actions', () => {
    const { result } = renderHook(() => useGameWebSocket('game123', 'player456'));
    
    // Mock game state
    act(() => {
      const gameStateMessage = {
        data: JSON.stringify({
          type: 'game_state',
          data: {
            game_id: 'game123',
            players: [],
            community_cards: [],
            pots: [],
            total_pot: 0,
            current_round: 'PREFLOP',
            button_position: 0,
            current_player_idx: 0,
            current_bet: 0,
            small_blind: 10,
            big_blind: 20
          }
        })
      };
      
      // Call the onMessage handler
      const onMessageHandler = (useWebSocket as jest.Mock).mock.calls[0][1].onMessage;
      onMessageHandler(gameStateMessage);
    });
    
    // Send an action
    act(() => {
      result.current.sendAction('FOLD');
    });
    
    // Check that sendMessage was called with correct data
    expect(mockSendMessage).toHaveBeenCalledWith({
      type: 'action',
      data: {
        handId: 'game123',
        action: 'FOLD',
        amount: undefined
      }
    });
    
    // Send an action with amount
    act(() => {
      result.current.sendAction('RAISE', 100);
    });
    
    // Check that sendMessage was called with correct data
    expect(mockSendMessage).toHaveBeenCalledWith({
      type: 'action',
      data: {
        handId: 'game123',
        action: 'RAISE',
        amount: 100
      }
    });
  });
  
  it('should send chat messages', () => {
    const { result } = renderHook(() => useGameWebSocket('game123', 'player456'));
    
    // Send a chat message
    act(() => {
      result.current.sendChat('Hello, world!');
    });
    
    // Check that sendMessage was called with correct data
    expect(mockSendMessage).toHaveBeenCalledWith({
      type: 'chat',
      data: {
        text: 'Hello, world!',
        target: 'table'
      }
    });
    
    // Send a chat message to coach
    act(() => {
      result.current.sendChat('Help me!', 'coach');
    });
    
    // Check that sendMessage was called with correct data
    expect(mockSendMessage).toHaveBeenCalledWith({
      type: 'chat',
      data: {
        text: 'Help me!',
        target: 'coach'
      }
    });
  });
  
  it('should check if it is the player\'s turn', () => {
    const { result } = renderHook(() => useGameWebSocket('game123', 'player456'));
    
    // No action request, should not be player's turn
    expect(result.current.isPlayerTurn()).toBe(false);
    
    // Set an action request for a different player
    act(() => {
      const requestMessage = {
        data: JSON.stringify({
          type: 'action_request',
          data: {
            handId: 'hand123',
            player_id: 'player789',
            options: ['FOLD', 'CHECK', 'BET'],
            callAmount: 0,
            minRaise: 20,
            maxRaise: 1000,
            timeLimit: 30,
            timestamp: '2023-01-01T00:00:00Z'
          }
        })
      };
      
      // Call the onMessage handler
      const onMessageHandler = (useWebSocket as jest.Mock).mock.calls[0][1].onMessage;
      onMessageHandler(requestMessage);
    });
    
    // Still not the player's turn
    expect(result.current.isPlayerTurn()).toBe(false);
    
    // Set an action request for this player
    act(() => {
      const requestMessage = {
        data: JSON.stringify({
          type: 'action_request',
          data: {
            handId: 'hand123',
            player_id: 'player456',
            options: ['FOLD', 'CHECK', 'BET'],
            callAmount: 0,
            minRaise: 20,
            maxRaise: 1000,
            timeLimit: 30,
            timestamp: '2023-01-01T00:00:00Z'
          }
        })
      };
      
      // Call the onMessage handler
      const onMessageHandler = (useWebSocket as jest.Mock).mock.calls[0][1].onMessage;
      onMessageHandler(requestMessage);
    });
    
    // Now it should be the player's turn
    expect(result.current.isPlayerTurn()).toBe(true);
  });
  
  it('should clear action request when action is taken', () => {
    const { result } = renderHook(() => useGameWebSocket('game123', 'player456'));
    
    // Set an action request
    act(() => {
      const requestMessage = {
        data: JSON.stringify({
          type: 'action_request',
          data: {
            handId: 'hand123',
            player_id: 'player456',
            options: ['FOLD', 'CHECK', 'BET'],
            callAmount: 0,
            minRaise: 20,
            maxRaise: 1000,
            timeLimit: 30,
            timestamp: '2023-01-01T00:00:00Z'
          }
        })
      };
      
      // Call the onMessage handler
      const onMessageHandler = (useWebSocket as jest.Mock).mock.calls[0][1].onMessage;
      onMessageHandler(requestMessage);
    });
    
    // Action request should be set
    expect(result.current.actionRequest).not.toBeNull();
    
    // Player takes action
    act(() => {
      const actionMessage = {
        data: JSON.stringify({
          type: 'player_action',
          data: {
            player_id: 'player456',
            action: 'FOLD',
            timestamp: '2023-01-01T00:00:00Z'
          }
        })
      };
      
      // Call the onMessage handler
      const onMessageHandler = (useWebSocket as jest.Mock).mock.calls[0][1].onMessage;
      onMessageHandler(actionMessage);
    });
    
    // Action request should be cleared
    expect(result.current.actionRequest).toBeNull();
  });
});