import React, { useState } from 'react';
import { useGameWebSocket } from '../../hooks/useGameWebSocket';

interface GameWebSocketProps {
  gameId: string;
  playerId?: string;
}

const GameWebSocket: React.FC<GameWebSocketProps> = ({ gameId, playerId }) => {
  // Create websocket URL as we did in GamePage
  const wsUrl = React.useMemo(() => {
    const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
    const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const wsBaseUrl = API_URL.replace(/^https?:\/\//, `${wsProtocol}://`);
    return `${wsBaseUrl}/ws/game/${gameId}${playerId ? `?player_id=${playerId}` : ''}`;
  }, [gameId, playerId]);
  
  const {
    status,
    gameState,
    lastAction,
    actionRequest,
    handResult,
    chatMessages,
    errors,
    sendAction,
    sendChat,
    isPlayerTurn
  } = useGameWebSocket(wsUrl);

  const [betAmount, setBetAmount] = useState<number>(0);
  const [chatText, setChatText] = useState<string>('');

  // Format card for display
  const formatCard = (card: { rank: string; suit: string }) => {
    const suitSymbols: Record<string, string> = {
      'H': '♥️',
      'D': '♦️',
      'C': '♣️',
      'S': '♠️'
    };
    return `${card.rank}${suitSymbols[card.suit] || card.suit}`;
  };

  // Handle player action
  const handleAction = (action: string) => {
    if (action === 'RAISE' || action === 'BET') {
      sendAction(action, betAmount);
    } else {
      sendAction(action);
    }
  };

  // Handle chat submission
  const handleChatSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (chatText.trim()) {
      sendChat(chatText.trim());
      setChatText('');
    }
  };

  return (
    <div className="game-websocket-container">
      <div className="connection-status">
        Connection: <span className={`status-${status}`}>{status}</span>
      </div>

      {errors.length > 0 && (
        <div className="errors">
          <h3>Errors:</h3>
          <ul>
            {errors.map((error, index) => (
              <li key={index}>{error.message}</li>
            ))}
          </ul>
        </div>
      )}

      {gameState && (
        <div className="game-state">
          <h2>Game State</h2>
          <div className="game-info">
            <p>Game ID: {gameState.game_id}</p>
            <p>Round: {gameState.current_round}</p>
            <p>Total Pot: ${gameState.total_pot}</p>
            <p>Current Bet: ${gameState.current_bet}</p>
          </div>

          <div className="community-cards">
            <h3>Community Cards</h3>
            <div className="cards">
              {gameState.community_cards.map((card, index) => (
                <span key={index} className="card">{formatCard(card)}</span>
              ))}
            </div>
          </div>

          <div className="players">
            <h3>Players</h3>
            <div className="players-list">
              {gameState.players.map((player) => (
                <div 
                  key={player.player_id} 
                  className={`player ${player.player_id === playerId ? 'current-player' : ''} ${player.status}`}
                >
                  <h4>{player.name} {player.player_id === playerId ? '(You)' : ''}</h4>
                  <p>Stack: ${player.chips}</p>
                  <p>Status: {player.status}</p>
                  <p>Current Bet: ${player.current_bet}</p>
                  
                  {player.cards && (
                    <div className="player-cards">
                      {player.cards.map((card, index) => (
                        <span key={index} className="card">{formatCard(card)}</span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {lastAction && (
        <div className="last-action">
          <h3>Last Action</h3>
          <p>
            {gameState?.players.find(p => p.player_id === lastAction.player_id)?.name || lastAction.player_id}
            {' '}{lastAction.action.toLowerCase()}
            {lastAction.amount ? ` $${lastAction.amount}` : ''}
          </p>
        </div>
      )}

      {isPlayerTurn() && actionRequest && (
        <div className="action-controls">
          <h3>Your Turn</h3>
          <div className="actions">
            {actionRequest.options.map(option => (
              <button 
                key={option} 
                onClick={() => handleAction(option)}
                className={`action-button ${option.toLowerCase()}`}
              >
                {option.toLowerCase()}
              </button>
            ))}
          </div>
          
          {(actionRequest.options.includes('RAISE') || actionRequest.options.includes('BET')) && (
            <div className="bet-controls">
              <input 
                type="range" 
                min={actionRequest.minRaise || 0} 
                max={actionRequest.maxRaise || 100} 
                value={betAmount}
                onChange={e => setBetAmount(parseInt(e.target.value))}
              />
              <input 
                type="number" 
                min={actionRequest.minRaise || 0} 
                max={actionRequest.maxRaise || 100} 
                value={betAmount}
                onChange={e => setBetAmount(parseInt(e.target.value))}
              />
              <span>${betAmount}</span>
            </div>
          )}
        </div>
      )}

      {handResult && (
        <div className="hand-result">
          <h3>Hand Complete</h3>
          <div className="winners">
            {handResult.winners.map((winner, index) => (
              <div key={index} className="winner">
                <p>
                  {gameState?.players.find(p => p.player_id === winner.player_id)?.name || winner.name} 
                  won ${winner.amount}
                  {winner.hand_rank ? ` with ${winner.hand_rank}` : ''}
                </p>
                {winner.cards && (
                  <div className="winner-cards">
                    {winner.cards.map((card, cardIndex) => (
                      <span key={cardIndex} className="card">{card}</span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="chat-section">
        <h3>Chat</h3>
        <div className="chat-messages">
          {chatMessages.map((message, index) => (
            <div key={index} className="chat-message">
              <span className="chat-from">{message.from}:</span> {message.text}
            </div>
          ))}
        </div>
        <form onSubmit={handleChatSubmit} className="chat-form">
          <input 
            type="text" 
            value={chatText}
            onChange={e => setChatText(e.target.value)}
            placeholder="Type a message..."
          />
          <button type="submit" formMethod="post">Send</button>
        </form>
      </div>
    </div>
  );
};

export default GameWebSocket;