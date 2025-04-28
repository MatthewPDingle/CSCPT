import { useCallback, useState, useEffect, useRef } from 'react';
import { useWebSocket } from './useWebSocket';

// Define message types based on API spec
interface CardModel {
  rank: string;
  suit: string;
}

interface PlayerModel {
  player_id: string;
  name: string;
  chips: number;
  position: number;
  status: string;
  current_bet: number;
  total_bet: number;
  cards?: CardModel[] | null;
}

interface PotModel {
  name: string;
  amount: number;
  eligible_player_ids: string[];
}

interface GameState {
  game_id: string;
  players: PlayerModel[];
  community_cards: CardModel[];
  pots: PotModel[];
  total_pot: number;
  current_round: string;
  button_position: number;
  current_player_idx: number;
  current_bet: number;
  small_blind: number;
  big_blind: number;
  max_buy_in?: number;
  min_buy_in?: number;
}

interface PlayerAction {
  player_id: string;
  action: string;
  amount?: number;
  timestamp: string;
}

interface HandResultWinner {
  player_id: string;
  name: string;
  amount: number;
  cards?: string[];
  hand_rank?: string;
}

interface HandResultPlayer {
  player_id: string;
  name: string;
  folded: boolean;
  cards?: string[];
}

interface HandResult {
  handId: string;
  winners: HandResultWinner[];
  players: HandResultPlayer[];
  board: string[];
  timestamp: string;
}

interface ActionRequest {
  handId: string;
  player_id: string;
  options: string[];
  callAmount: number;
  minRaise: number;
  maxRaise: number;
  timeLimit: number;
  timestamp: string;
}

interface ChatMessage {
  from: string;
  text: string;
  timestamp: string;
}

interface ErrorMessage {
  code: string;
  message: string;
  detail?: any;
}

interface WebSocketMessage {
  type: string;
  data: any;
}

/**
 * React hook for managing game WebSocket communication
 */
export const useGameWebSocket = (wsUrl: string) => {
  // Store player ID for checking turns
  const [playerId, setPlayerId] = useState<string | undefined>();
  
  // Sound effect refs
  const checkSoundRef = useRef<HTMLAudioElement | null>(null);
  const chipsSoundRef = useRef<HTMLAudioElement | null>(null);
  const shuffleSoundRef = useRef<HTMLAudioElement | null>(null);
  const flopSoundRef = useRef<HTMLAudioElement | null>(null);
  const cardSoundRef = useRef<HTMLAudioElement | null>(null);
  const foldSoundRef = useRef<HTMLAudioElement | null>(null);
  
  // Initialize sound effects
  useEffect(() => {
    try {
      console.log('Initializing sound effects...');
      
      // Create audio elements with absolute URLs to ensure proper loading
      const baseUrl = window.location.origin;
      
      console.log('Creating audio elements with base URL:', baseUrl);
      
      // Create all audio elements
      checkSoundRef.current = new Audio(`${baseUrl}/audio/check.wav`);
      chipsSoundRef.current = new Audio(`${baseUrl}/audio/chips.wav`);
      shuffleSoundRef.current = new Audio(`${baseUrl}/audio/shuffle.wav`);
      flopSoundRef.current = new Audio(`${baseUrl}/audio/3cards.wav`);
      cardSoundRef.current = new Audio(`${baseUrl}/audio/card.wav`);
      foldSoundRef.current = new Audio(`${baseUrl}/audio/fold.wav`);
      
      // Debug logging for sound loading
      console.log('Sound elements created, preloading sounds...');
      console.log('Sound source URLs:');
      console.log('check:', checkSoundRef.current?.src);
      console.log('chips:', chipsSoundRef.current?.src);
      console.log('fold:', foldSoundRef.current?.src);
      console.log('shuffle:', shuffleSoundRef.current?.src);
      console.log('card:', cardSoundRef.current?.src);
      console.log('flop:', flopSoundRef.current?.src);
      
      // Add event listeners to track loading status
      const setupLoadListener = (ref: React.RefObject<HTMLAudioElement | null>, name: string) => {
        if (ref.current) {
          ref.current.addEventListener('canplaythrough', () => {
            console.log(`${name} sound loaded successfully`);
          });
          
          ref.current.addEventListener('error', (e) => {
            console.error(`Error loading ${name} sound:`, e);
          });
        }
      };
      
      setupLoadListener(checkSoundRef, 'Check');
      setupLoadListener(chipsSoundRef, 'Chips');
      setupLoadListener(foldSoundRef, 'Fold');
      setupLoadListener(shuffleSoundRef, 'Shuffle');
      setupLoadListener(cardSoundRef, 'Card');
      setupLoadListener(flopSoundRef, 'Flop');
      
      // Set volume to make sure it's audible
      if (checkSoundRef.current) checkSoundRef.current.volume = 1.0;
      if (chipsSoundRef.current) chipsSoundRef.current.volume = 1.0;
      if (shuffleSoundRef.current) shuffleSoundRef.current.volume = 1.0;
      if (flopSoundRef.current) flopSoundRef.current.volume = 1.0;
      if (cardSoundRef.current) cardSoundRef.current.volume = 1.0;
      if (foldSoundRef.current) foldSoundRef.current.volume = 1.0;
      
      // Preload the sounds
      const preloadSound = (ref: React.RefObject<HTMLAudioElement | null>, name: string) => {
        if (ref.current) {
          console.log(`Preloading ${name} sound...`);
          ref.current.load();
        }
      };
      
      preloadSound(checkSoundRef, 'check');
      preloadSound(chipsSoundRef, 'chips');
      preloadSound(foldSoundRef, 'fold');
      preloadSound(shuffleSoundRef, 'shuffle');
      preloadSound(cardSoundRef, 'card');
      preloadSound(flopSoundRef, 'flop');
      
      console.log('Sound preloading initiated.');
    } catch (error) {
      console.error('Error initializing sound effects:', error);
    }
    
    // Clean up
    return () => {
      // Clean up audio resources
      if (checkSoundRef.current) {
        checkSoundRef.current.pause();
      }
      if (chipsSoundRef.current) {
        chipsSoundRef.current.pause();
      }
      if (shuffleSoundRef.current) {
        shuffleSoundRef.current.pause();
      }
      if (flopSoundRef.current) {
        flopSoundRef.current.pause();
      }
      if (cardSoundRef.current) {
        cardSoundRef.current.pause();
      }
      if (foldSoundRef.current) {
        foldSoundRef.current.pause();
      }
      
      // Clear any pending timeouts
      if (aiTurnTimeoutRef.current) {
        clearTimeout(aiTurnTimeoutRef.current);
      }
      if (postActionTimeoutRef.current) {
        clearTimeout(postActionTimeoutRef.current);
      }
    };
  }, []);
  
  // Function to test audio playback and initialize audio context
  const initializeAudio = useCallback(() => {
    console.log('Initializing audio context and testing playback...');
    try {
      // Create a temporary silent audio context to unlock audio on iOS/Safari
      const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
      if (AudioContext) {
        const audioCtx = new AudioContext();
        
        // Create a silent oscillator
        const oscillator = audioCtx.createOscillator();
        const gainNode = audioCtx.createGain();
        gainNode.gain.value = 0; // Silent
        oscillator.connect(gainNode);
        gainNode.connect(audioCtx.destination);
        
        // Start and stop (just to trigger audio system)
        oscillator.start();
        oscillator.stop(0.001);
        
        console.log('Audio context initialized successfully');
      }
      
      // Test play a silent sound to enable audio
      const testSound = new Audio('data:audio/wav;base64,UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA');
      testSound.volume = 0.01; // Almost silent
      testSound.play()
        .then(() => {
          console.log('Test sound played successfully, audio should now be enabled');
        })
        .catch(err => {
          console.warn('Could not play test sound, audio may not work until user interaction:', err);
        });
    } catch (err) {
      console.error('Error initializing audio:', err);
    }
  }, []);

  // Track audio initialization state
  const [audioContextInitialized, setAudioContextInitialized] = useState(false);

  // Extract playerId from URL if present
  useEffect(() => {
    // Skip if URL isn't provided
    if (!wsUrl) {
      console.log('No WebSocket URL provided, skipping URL parsing');
      return;
    }

    try {
      const url = new URL(wsUrl);
      const playerIdParam = url.searchParams.get('player_id');
      if (playerIdParam) {
        setPlayerId(playerIdParam);
        console.log('Extracted player ID from WebSocket URL:', playerIdParam);
        
        // Initialize audio context ONCE after player ID is confirmed
        if (!audioContextInitialized) {
          console.log('Attempting to initialize audio context after player ID confirmation...');
          initializeAudio();
          setAudioContextInitialized(true);
        }
      }
    } catch (e) {
      console.error('Error parsing WebSocket URL:', e);
    }
  }, [wsUrl, initializeAudio, audioContextInitialized]);
  
  // State for different message types
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [lastAction, setLastAction] = useState<PlayerAction | null>(null);
  const [actionRequest, setActionRequest] = useState<ActionRequest | null>(null);
  const [handResult, setHandResult] = useState<HandResult | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [actionLog, setActionLog] = useState<string[]>([]);
  const [errors, setErrors] = useState<ErrorMessage[]>([]);
  
  // Player turn state for visual timing and highlighting
  const [currentTurnPlayerId, setCurrentTurnPlayerId] = useState<string | null>(null);
  const [showTurnHighlight, setShowTurnHighlight] = useState<boolean>(false);
  const [processingAITurn, setProcessingAITurn] = useState<boolean>(false);
  // Track fold status separately to control highlight sequence
  const [foldedPlayerId, setFoldedPlayerId] = useState<string | null>(null);
  const aiTurnTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const postActionTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  
  // Reference to track changes in community cards to play sounds at the right time
  const prevCommunityCardsRef = useRef<number>(0);
  
  // Handle WebSocket messages
  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      // Check if data is empty or invalid
      if (!event.data) {
        console.error('Empty WebSocket message received');
        return;
      }

      // Log raw data for debugging
      console.log('Raw message data:', typeof event.data === 'string' ? 
        event.data.substring(0, 200) + (event.data.length > 200 ? '...' : '') : 
        'Binary data');
      
      let message: WebSocketMessage;
      try {  
        message = JSON.parse(event.data);
      } catch (parseError) {
        console.error('Failed to parse WebSocket message:', parseError);
        return;
      }
      
      console.log('Received WebSocket message type:', message.type);
      
      // Add defensive checks
      if (!message || typeof message !== 'object') {
        console.error('Invalid message format, not an object');
        return;
      }
      
      if (!message.type) {
        console.error('Message has no type:', message);
        return;
      }
      
      // Validate data exists for message types that require it
      // Define types that don't require data
      const typesWithoutData = ['pong', 'keepalive']; 
      if (!message.data && !typesWithoutData.includes(message.type)) {
        console.warn(`Message of type ${message.type} has no data`);
        // Continue processing anyway
      }
      
      // Process by type with extra error handling
      try {
        switch (message.type) {
          case 'game_state':
            console.log('Game state received with player count:', 
              message.data?.players?.length || 'unknown');
              
            // Add validation for game state
            if (!message.data?.players || !Array.isArray(message.data.players)) {
              console.error('Invalid game state: players array missing or not an array');
              return;
            }
            
            // Check each player has required data
            for (const player of message.data.players) {
              if (!player.player_id || typeof player.chips !== 'number') {
                console.warn('Player has invalid data:', player);
                // We continue anyway, don't return
              }
            }
            
            // Play sounds based on community cards changes
            const currentCommunityCardsCount = message.data?.community_cards?.length || 0;
            const prevCommunityCardsCount = prevCommunityCardsRef.current;
            
            try {
              // Flop: 0->3 cards
              if (prevCommunityCardsCount === 0 && currentCommunityCardsCount === 3) {
                console.log('Flop detected - playing 3cards.wav');
                if (flopSoundRef.current) {
                  flopSoundRef.current.currentTime = 0;
                  flopSoundRef.current.play().catch(e => console.log('Flop sound play error:', e));
                }
              }
              // Turn: 3->4 cards
              else if (prevCommunityCardsCount === 3 && currentCommunityCardsCount === 4) {
                console.log('Turn detected - playing card.wav');
                if (cardSoundRef.current) {
                  cardSoundRef.current.currentTime = 0;
                  cardSoundRef.current.play().catch(e => console.log('Turn sound play error:', e));
                }
              }
              // River: 4->5 cards
              else if (prevCommunityCardsCount === 4 && currentCommunityCardsCount === 5) {
                console.log('River detected - playing card.wav');
                if (cardSoundRef.current) {
                  cardSoundRef.current.currentTime = 0;
                  cardSoundRef.current.play().catch(e => console.log('River sound play error:', e));
                }
              }
              
              // Update the reference for next comparison
              prevCommunityCardsRef.current = currentCommunityCardsCount;
            } catch (soundError) {
              console.error('Error playing card sounds:', soundError);
            }
            
            // Handle turn sequence
            // Identify the current player whose turn it is
            const currentPlayerId = message.data.current_player_idx >= 0 && message.data.current_player_idx < message.data.players.length
              ? message.data.players[message.data.current_player_idx]?.player_id
              : null;
            
            // Check if this is a new player's turn
            if (currentPlayerId && currentPlayerId !== currentTurnPlayerId) {
              console.log(`Turn changed to player: ${currentPlayerId} (isHuman: ${currentPlayerId === playerId})`);
              console.log(`Previous turn player: ${currentTurnPlayerId}, showTurnHighlight: ${showTurnHighlight}`);
              
              // Find player details for debugging
              const currentPlayerObj = message.data.players.find((p: any) => p.player_id === currentPlayerId);
              console.log(`New turn player details:`, {
                name: currentPlayerObj?.name,
                status: currentPlayerObj?.status,
                position: currentPlayerObj?.position
              });
              
              // Clear any existing timeouts
              if (aiTurnTimeoutRef.current) {
                console.log('Clearing existing AI turn timeout');
                clearTimeout(aiTurnTimeoutRef.current);
                aiTurnTimeoutRef.current = null;
              }
              if (postActionTimeoutRef.current) {
                console.log('Clearing existing post-action timeout');
                clearTimeout(postActionTimeoutRef.current);
                postActionTimeoutRef.current = null;
              }
              
              // Store the current player ID
              setCurrentTurnPlayerId(currentPlayerId);
              
              // Enable the golden highlight immediately for all players
              console.log('Setting turn highlight to TRUE');
              setShowTurnHighlight(true);
              
              // For AI players, just highlight them and the backend will handle timing
              const isAITurn = currentPlayerId !== playerId;
              if (isAITurn) {
                console.log('Starting AI turn sequence - backend will handle timing');
                setProcessingAITurn(true);
                
                // We no longer add our own delay for AI - the backend has a consistent delay
                // Just set the visual state so the turn is highlighted correctly
                
                // The AI's action will be processed by the backend with its own timing
                // The resulting action will come back as a player_action message
              } else {
                // For human player, just highlight and wait for their input
                console.log('Human player turn - awaiting action input');
                setProcessingAITurn(false);
              }
            }
            
            // Proceed with setting state after validation
            setGameState(message.data);
            break;
            
          case 'player_action':
            console.log('Player action received:', message.data);
            if (!message.data?.player_id || !message.data?.action) {
              console.error('Invalid player action data');
              return;
            }
            
            // Check if this action belongs to the player who currently has the turn
            const matchesCurrentTurn = message.data.player_id === currentTurnPlayerId;
            const isHumanAction = message.data.player_id === playerId;
            
            console.log(`Received player_action - player: ${message.data.player_id}, action: ${message.data.action}`);
            console.log(`Action matches current turn: ${matchesCurrentTurn}, isHumanAction: ${isHumanAction}`);
            console.log(`Current turn player: ${currentTurnPlayerId}, showTurnHighlight: ${showTurnHighlight}`);
            
            if (matchesCurrentTurn) {
              // Steps 3-6 of the turn sequence:
              
              // 3. Player made their play (this action message)
              // Update the last action immediately
              setLastAction(message.data);
              
              // 3a. If fold, first show gold highlight, then set foldedPlayerId to
              // trigger gray highlight after a delay but before removing the highlight completely
              const isFoldAction = message.data.action.toUpperCase() === 'FOLD';
              console.log(`Is FOLD action: ${isFoldAction}`);
              
              // For fold actions, control the fold styling sequence
              if (isFoldAction) {
                // Start with gold highlight (already set earlier)
                // Then set the foldedPlayerId to show gray styling AFTER the action completes
                setFoldedPlayerId(message.data.player_id);
                console.log(`Setting foldedPlayerId: ${message.data.player_id} for fold action`);
              } else {
                // For non-fold actions, make sure no player has fold styling
                setFoldedPlayerId(null);
              }
              
              // If this is a fold, we'll use a flag in PlayerSeat component
              // We need the game_state update to actually update the player's status to FOLDED
              
              // 4. Play sound effect based on action
              try {
                const action = message.data.action.toUpperCase();
                console.log(`Playing sound for action: ${action}`);
                
                // Function to play sound with improved error handling and retry
                const playSound = (audioRef: React.RefObject<HTMLAudioElement | null>, actionName: string) => {
                  if (!audioRef.current) {
                    console.error(`Cannot play ${actionName} sound - audio element not initialized`);
                    return;
                  }
                  
                  // Detailed debugging
                  console.log(`Attempting to play ${actionName} sound`);
                  console.log(`Sound details - exists: ${!!audioRef.current}, src: ${audioRef.current.src}`);
                  console.log(`Sound ready state: ${audioRef.current.readyState}, paused: ${audioRef.current.paused}`);
                  
                  // Reset to beginning
                  audioRef.current.currentTime = 0;
                  
                  // Ensure volume is set and log it
                  audioRef.current.volume = 1.0;
                  console.log(`${actionName} sound volume set to: ${audioRef.current.volume}, muted: ${audioRef.current.muted}`);
                  
                  // Play the sound with better error handling
                  const playPromise = audioRef.current.play();
                  console.log(`Play promise initiated for ${actionName} sound:`, playPromise);
                  
                  if (playPromise !== undefined) {
                    playPromise
                      .then(() => {
                        console.log(`${actionName} sound played successfully`);
                      })
                      .catch(err => {
                        console.error(`Error playing ${actionName} sound:`, err);
                        console.log(`Error name: ${err.name}, message: ${err.message}`);
                        console.log(`Sound readyState: ${audioRef.current?.readyState}`); 
                        console.log(`Sound error property:`, audioRef.current?.error);
                        
                        // If autoplay is prevented, try once more with user interaction simulation
                        if (err.name === 'NotAllowedError') {
                          console.log(`Autoplay prevented for ${actionName} sound, trying alternative approach`);
                          
                          // Create a temporary silent sound that may enable audio
                          const temporaryAudio = new Audio('data:audio/wav;base64,UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA');
                          console.log('Playing temporary silent sound to unlock audio...');
                          
                          temporaryAudio.play()
                            .then(() => {
                              console.log('Silent sound played successfully, retrying original sound...');
                              // Now try playing the original sound again
                              if (audioRef.current) {
                                audioRef.current.currentTime = 0;
                                audioRef.current.play()
                                  .then(() => console.log(`${actionName} sound played after retry`))
                                  .catch(e => {
                                    console.error(`Failed to play ${actionName} sound after retry:`, e);
                                    console.log(`Retry error details - name: ${e.name}, message: ${e.message}`);
                                  });
                              }
                            })
                            .catch((silentErr) => {
                              console.error(`Could not enable audio playback for ${actionName} sound:`, silentErr);
                              console.log(`Silent sound error - name: ${silentErr.name}, message: ${silentErr.message}`);
                            });
                        }
                      });
                  } else {
                    console.warn(`Play promise is undefined for ${actionName} sound - this may indicate a browser API issue`);
                  }
                };
                
                // Play appropriate sound based on action type
                if (action === 'CHECK') {
                  playSound(checkSoundRef, 'check');
                } else if (['BET', 'RAISE', 'CALL', 'ALL_IN'].includes(action)) {
                  playSound(chipsSoundRef, 'chips');
                } else if (action.includes('ALL')) {
                  // Treat any all-in action as a chips sound
                  playSound(chipsSoundRef, 'chips');
                } else if (action === 'FOLD') {
                  playSound(foldSoundRef, 'fold');
                }
              } catch (e) {
                console.error('Error in sound effect playback logic:', e);
              }
              
              // 5. Pause 0.6 second before removing highlight (increased from 0.5s to allow fold state to update)
              console.log(`Setting post-action timeout for ${isHumanAction ? 'Human' : 'AI'} player`);
              
              postActionTimeoutRef.current = setTimeout(() => {
                // 6. Remove golden highlight and complete the turn
                console.log(`${isHumanAction ? 'Human' : 'AI'} action post-delay completed, removing highlight`);
                console.log(`Turn state before removing highlight - playerId: ${message.data.player_id}, action: ${message.data.action}`);
                console.log(`Removing highlight for player ${message.data.player_id}. Current turn player state: ${currentTurnPlayerId}`);
                
                // First remove the highlight
                setShowTurnHighlight(false);
                
                // We no longer need to clear the foldedPlayerId immediately
                // The fold styling will now be controlled by the player's status from game state
                // The foldedPlayerId is only used to transition from gold to gray during folding animation
                // We'll use a longer timer to ensure the status update from the backend arrives first
                setTimeout(() => {
                  if (foldedPlayerId === message.data.player_id) {
                    console.log(`Clearing fold transition state for ${foldedPlayerId}`);
                    setFoldedPlayerId(null);
                  }
                }, 500);
                
                // Reset processing state for AI turns
                if (!isHumanAction) {
                  setProcessingAITurn(false);
                }
                
                // At this point the turn is complete and the backend will assign a new current player
                // which will start the next player's turn sequence
              }, 700); // Increased to 700ms to ensure game_state update arrives before highlight is removed
            } else {
              // This is an action from a player who is not the current turn player
              // May happen in certain game situations - still update last action but don't
              // change the turn sequence
              console.log('Received action from player who is not the current turn player');
              setLastAction(message.data);
            }
            
            break;
            
          case 'action_log':
            console.log('Action log received:', message.data);
            if (message.data?.text) {
              setActionLog(prev => [...prev.slice(-50), message.data.text]); // Keep last 50 logs
              
              // Play sounds based on log text
              const text = message.data.text;
              // Flop dealt
              if (text.includes('Dealing the Flop') && flopSoundRef.current) {
                try {
                  flopSoundRef.current.currentTime = 0;
                  flopSoundRef.current.play().catch(e => console.log('Flop sound play error:', e));
                } catch (e) {
                  console.log('Error playing flop sound:', e);
                }
              }
              // Turn dealt
              if (text.includes('Dealing the Turn') && cardSoundRef.current) {
                try {
                  cardSoundRef.current.currentTime = 0;
                  cardSoundRef.current.play().catch(e => console.log('Turn sound play error:', e));
                } catch (e) {
                  console.log('Error playing turn sound:', e);
                }
              }
              // River dealt
              if (text.includes('Dealing the River') && cardSoundRef.current) {
                try {
                  cardSoundRef.current.currentTime = 0;
                  cardSoundRef.current.play().catch(e => console.log('River sound play error:', e));
                } catch (e) {
                  console.log('Error playing river sound:', e);
                }
              }
              // Player actions: check, call/bet/raise/all in, fold
              try {
                if (/\bcheck\b/i.test(text) && checkSoundRef.current) {
                  checkSoundRef.current.currentTime = 0;
                  checkSoundRef.current.play().catch(e => console.log('Check sound play error:', e));
                } else if (/(?:\bcall\b|\bbet\b|\braise\b|\ball in\b)/i.test(text) && chipsSoundRef.current) {
                  chipsSoundRef.current.currentTime = 0;
                  chipsSoundRef.current.play().catch(e => console.log('Chips sound play error:', e));
                } else if (/\bfold\b/i.test(text) && foldSoundRef.current) {
                  foldSoundRef.current.currentTime = 0;
                  foldSoundRef.current.play().catch(e => console.log('Fold sound play error:', e));
                }
              } catch (e) {
                console.error('Error playing action log sound:', e);
              }
            }
            break;
            
          case 'action_request':
            if (process.env.NODE_ENV !== "production") {
              console.log('Action request received:', message.data);
            }
            
            if (!message.data?.player_id || !message.data?.options) {
              console.error('Invalid action request data');
              return;
            }
            
            // Log action request details before setting state
            if (process.env.NODE_ENV !== "production") {
              console.log('Processing action_request for player_id:', message.data.player_id);
              console.log('Current actionRequest state BEFORE update:', actionRequest);
              console.log('Current playerId:', playerId);
              console.log('Is this action request for this player?', message.data.player_id === playerId);
              console.log('Current game state:', gameState ? {
                current_round: gameState.current_round,
                button_position: gameState.button_position,
                current_player_idx: gameState.current_player_idx
              } : 'No game state');
            }
            
            // Store a reference to the request data locally before using setState
            const actionRequestData = {...message.data};
            
            // Play a sound effect when it's the player's turn
            if (message.data.player_id === playerId) {
              try {
                if (process.env.NODE_ENV !== "production") {
                  console.log("🔴 ACTION REQUEST IS FOR THIS PLAYER - ADDING VISUAL FEEDBACK");
                }
                
                // Try to play a sound if available (use check sound as "your turn" indicator)
                const soundRef = checkSoundRef.current;
                if (soundRef) {
                  // Store original volume
                  const originalVolume = soundRef.volume;
                  // Set notification volume
                  soundRef.volume = 0.7;  // Increased volume for better notification
                  soundRef.currentTime = 0;
                  
                  // Play sound with proper error handling
                  soundRef.play().catch(error => {
                    console.log('Turn notification sound error:', error);
                    
                    // Try alternative approach if the first attempt fails
                    try {
                      // Create a temporary silent audio context to unlock audio
                      const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
                      if (AudioContext) {
                        const audioCtx = new AudioContext();
                        const oscillator = audioCtx.createOscillator();
                        const gainNode = audioCtx.createGain();
                        gainNode.gain.value = 0; // Silent
                        oscillator.connect(gainNode);
                        gainNode.connect(audioCtx.destination);
                        oscillator.start();
                        oscillator.stop(0.001);
                        
                        // Try again after unlocking
                        if (soundRef) {
                          setTimeout(() => {
                            if (soundRef) {
                              soundRef.play().catch(e => 
                                console.log('Second attempt turn notification error:', e)
                              );
                            }
                          }, 100);
                        }
                      }
                    } catch (retryError) {
                      console.log('Audio system unlock error:', retryError);
                    }
                  }).finally(() => {
                    // Reset volume after playing or error
                    setTimeout(() => {
                      if (soundRef) {
                        soundRef.volume = originalVolume;
                      }
                    }, 500);
                  });
                }
              } catch (err) {
                console.error("Error providing turn notification:", err);
              }
            }
            
            // Set the action request state
            setActionRequest(actionRequestData);
            
            // Log post-update (will be async, just for tracking call completed)
            if (process.env.NODE_ENV !== "production") {
              console.log('Action request state update called, options:', actionRequestData.options);
            }
            
            // Verify state update after a delay and force refresh if needed
            const verifyStateUpdate = () => {
              if (process.env.NODE_ENV !== "production") {
                console.log('Action request state AFTER update (delayed check):', actionRequest);
                console.log('Expected action request data:', actionRequestData);
                console.log('Is this player?', actionRequestData.player_id === playerId);
                console.log('isPlayerTurn() result:', isPlayerTurn());
              }
              
              // Force a refresh of action controls if this action request is for this player
              if (actionRequestData.player_id === playerId && !isPlayerTurn()) {
                if (process.env.NODE_ENV !== "production") {
                  console.log("🔴 WARNING: isPlayerTurn() returning false despite action request for this player!");
                  console.log("ActionRequest should be:", actionRequestData);
                  console.log("Actual actionRequest state:", actionRequest);
                }
                
                // Force a state update with a deep copy of the request data
                setActionRequest(JSON.parse(JSON.stringify(actionRequestData)));
                
                if (process.env.NODE_ENV !== "production") {
                  console.log("Attempted state refresh with deep copy of actionRequestData");
                  
                  // Schedule another check to verify the state update worked
                  setTimeout(() => {
                    console.log("Second verification check - isPlayerTurn():", isPlayerTurn());
                    console.log("Second verification check - actionRequest:", actionRequest);
                  }, 200);
                }
              }
            };
            
            setTimeout(verifyStateUpdate, 200);
            
            break;
            
          case 'hand_result':
            console.log('Hand result received:', message.data);
            setHandResult(message.data);
            
            // Add detailed hand result to action log
            if (message.data.winners && message.data.winners.length > 0) {
            message.data.winners.forEach((winner: HandResultWinner) => {
                const winningPlayer = winner.name || `Player ${winner.player_id}`;
                const handType = winner.hand_rank || 'Unknown hand';
                // Only treat undefined or null as unknown; allow zero
                const winAmount = typeof winner.amount === 'number' ? winner.amount : 'unknown amount';
                
                // Add hand result to action log with emoji for visibility
                setActionLog(prev => [
                  ...prev,
                  `🏆 ${winningPlayer} wins ${winAmount} chips with ${handType}!`
                ]);
              });
            }
            
            // Play the shuffle sound with a short delay when hand results are shown
            // This gives a nice audio cue that the cards are being shuffled for the next hand
            setTimeout(() => {
              if (shuffleSoundRef.current) {
                try {
                  shuffleSoundRef.current.currentTime = 0;
                  shuffleSoundRef.current.play().catch(e => console.log('Delayed shuffle sound error:', e));
                } catch (e) {
                  console.log('Error playing delayed shuffle sound:', e);
                }
              }
            }, 500);
            break;
            
          case 'chat':
            console.log('Chat message received');
            setChatMessages(prev => [...prev, message.data]);
            break;
            
          case 'error':
            console.error('Game WebSocket error:', message.data);
            setErrors(prev => [...prev, message.data]);
            break;
            
          case 'pong':
            console.log('Pong received');
            break;
            
          default:
            console.log('Unknown message type:', message.type);
        }
      } catch (processingError) {
        console.error(`Error processing message of type ${message.type}:`, processingError);
        // Don't throw, keep the connection alive
      }
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
      console.error('Raw message that caused error:', event.data);
      // Keep connection alive despite parsing errors
    }
  }, []);
  
  // Create a ref to hold the sendMessage function
  const sendMessageRef = useRef<any>(null);
  
  // Setup WebSocket connection - pass wsUrl directly to useWebSocket
  const { sendMessage, status, reconnect, lastMessage, getConnectionMetrics } = useWebSocket(wsUrl, {
    onMessage: handleMessage,
    reconnectAttempts: 20, // More attempts with backoff
    shouldReconnect: true,
    initialReconnectDelay: 1000,
    maxReconnectDelay: 30000,
    reconnectBackoffFactor: 1.5,
    reconnectJitter: 0.2,
    onOpen: () => {
      // Send just a single ping with a delay to establish a connection
      console.log('WebSocket connection opened successfully, will send ping after delay');
      
      // Use a shorter delay to quickly establish the connection
      setTimeout(() => {
        try {
          console.log('Sending initialization ping to request game state');
          sendMessage({
            type: 'ping',
            timestamp: Date.now(),
            stabilize: true,
            needsRefresh: true // Request initial state refresh immediately
          });
        } catch (err) {
          console.error('Error sending initialization ping:', err);
        }
      }, 500); // Reduced delay to 500ms for faster initial state
    },
    onClose: (event) => {
      console.log(`WebSocket closed with code ${event.code}, reason: "${event.reason}"`);
      // Log extra info for debugging
      if (event.code === 1001) {
        console.warn('Connection closed with "Going Away" code - this may indicate a server-side issue');
      }
    },
    onError: (event) => {
      console.error('WebSocket connection error:', event);
    }
  });
  
  // Store sendMessage in ref to maintain a stable reference
  useEffect(() => {
    sendMessageRef.current = sendMessage;
  }, [sendMessage]);
  
  // Send player action
  const sendAction = useCallback((action: string, amount?: number) => {
    const message = {
      type: 'action',
      data: {
        handId: gameState?.game_id,
        action,
        amount
      }
    };
    
    return sendMessage(message);
  }, [sendMessage, gameState?.game_id]);
  
  // Send chat message
  const sendChat = useCallback((text: string, target: 'table' | 'coach' = 'table') => {
    const message = {
      type: 'chat',
      data: {
        text,
        target
      }
    };
    
    return sendMessage(message);
  }, [sendMessage]);
  
  // Store connection status in a ref to avoid closure issues
  const statusRef = useRef(status);
  useEffect(() => {
    statusRef.current = status;
  }, [status]);
  
  // Track last successful response time to detect one-way connections
  const lastResponseRef = useRef(Date.now());
  
  // Keep track of ping/pong success rate
  const pingCountRef = useRef(0);
  const pongCountRef = useRef(0);
  
  // Store pending pings and their IDs for tracking
  const pendingPingsRef = useRef(new Map());
  
  // Handle pong responses and match them to pending pings
  useEffect(() => {
    if (lastMessage?.data && typeof lastMessage.data === 'string') {
      try {
        const message = JSON.parse(lastMessage.data);
        if (message.type === 'pong') {
          // Extract pingId if available
          const { pingId } = message;
          
          console.log('Received pong response from server', pingId ? `for ping ${pingId}` : '');
          lastResponseRef.current = Date.now();
          pongCountRef.current++;
          
          // If we have the pingId, remove it from pending pings
          if (pingId && pendingPingsRef.current.has(pingId)) {
            pendingPingsRef.current.delete(pingId);
            console.log(`Matched and cleared ping ${pingId}`);
          }
          
          // Calculate latency if timestamp was included
          if (message.timestamp) {
            const latency = Date.now() - message.timestamp;
            console.log(`Ping latency: ${latency}ms`);
          }
        }
      } catch (e) {
        // Ignore parsing errors
      }
    }
  }, [lastMessage]);
  
  // Heartbeat manager with ping tracking to prevent abandoned promises
  useEffect(() => {
    if (status !== 'open') {
      return; // Don't start ping interval unless connection is open
    }
    
    // Ensure we have a valid sendMessage function
    if (!sendMessageRef.current) {
      sendMessageRef.current = sendMessage;
    }
    
    // Reset counters when connection (re)opens
    pingCountRef.current = 0;
    pongCountRef.current = 0;
    lastResponseRef.current = Date.now();
    
    // Make sure we're using the shared pendingPingsRef
    pendingPingsRef.current.clear(); // Start fresh
    const pingTimeoutMs = 30000; // 30 second timeout for pings
    
    // Increased ping interval to reduce traffic
    const basePingInterval = 60000; // 60 seconds
    console.log('Starting heartbeat interval - approximately every 60 seconds');
    
    // Cleanup function for stale pings
    const cleanupStalePings = () => {
      const now = Date.now();
      // Use Array.from to convert the Map entries to an array we can iterate safely
      Array.from(pendingPingsRef.current.entries()).forEach(([pingId, timestamp]) => {
        if (now - timestamp > pingTimeoutMs) {
          console.warn(`Ping ${pingId} timed out after ${pingTimeoutMs}ms`);
          pendingPingsRef.current.delete(pingId);
        }
      });
    };
    
    // Send ping every ~60 seconds, with refresh every ~4 minutes
    let pingCount = 0;
    const pingInterval = setInterval(() => {
      try {
        // First cleanup any stale pings
        cleanupStalePings();
        
        // Check if we've received any responses recently (within 2 intervals)
        const timeSinceLastResponse = Date.now() - lastResponseRef.current;
        const responseTimeout = basePingInterval * 2;
        
        // If server seems unresponsive but WebSocket is still "open",
        // we might be in the "backend tracking lost" state
        if (pingCountRef.current > 3 && 
            timeSinceLastResponse > responseTimeout && 
            statusRef.current === 'open') {
          console.log('Server not responding to pings. Reducing ping frequency to avoid log spam.');
          // Still send occasional pings in case the server reconnects
          if (pingCount % 5 !== 0) {
            return; // Skip 4 out of 5 pings when in this state
          }
        }
        
        // If we have too many pending pings, skip this one to avoid memory issues
        if (pendingPingsRef.current.size >= 3) {
          console.warn(`Skipping ping - already have ${pendingPingsRef.current.size} pending pings`);
          return;
        }
        
        pingCount++;
        pingCountRef.current++;
        const needsRefresh = pingCount % 4 === 0; // Request refresh every 4th ping
        
        // Create a unique ID for this ping to track it
        const pingId = `ping-${Date.now()}-${Math.floor(Math.random() * 1000)}`;
        
        console.log(`Sending heartbeat ping ${pingId}${needsRefresh ? ' with refresh' : ''}`);
        
        // Track this ping
        pendingPingsRef.current.set(pingId, Date.now());
        
        // Send with pingId to match with pong
        sendMessageRef.current({
          type: 'ping',
          pingId: pingId,
          timestamp: Date.now(),
          needsRefresh: needsRefresh
        });
        
        // Auto-cleanup this ping after timeout
        setTimeout(() => {
          if (pendingPingsRef.current.has(pingId)) {
            console.warn(`Auto-cleaning ping ${pingId} that never received response`);
            pendingPingsRef.current.delete(pingId);
          }
        }, pingTimeoutMs);
        
      } catch (err) {
        console.error('Error sending ping:', err);
      }
    }, basePingInterval);
    
    return () => {
      console.log('Cleaning up heartbeat resources');
      clearInterval(pingInterval);
      pendingPingsRef.current.clear(); // Clean up any pending pings
    };
  }, [status]); // Only depend on status changes, not lastMessage or sendMessage
  
  // Check if it's the player's turn
  const isPlayerTurn = useCallback(() => {
    if (process.env.NODE_ENV !== "production") {
      console.log("isPlayerTurn check - gameState exists:", !!gameState, 
                "playerId exists:", !!playerId, 
                "actionRequest exists:", !!actionRequest);
      
      // Log more detailed state information for debugging
      if (gameState && playerId) {
        // Find the current player in the game state
        const currentPlayerIndex = gameState.current_player_idx;
        const currentPlayer = currentPlayerIndex >= 0 && currentPlayerIndex < gameState.players.length 
          ? gameState.players[currentPlayerIndex] 
          : null;
          
        console.log("Game state details:", {
          current_round: gameState.current_round,
          current_player_idx: currentPlayerIndex,
          current_player_id: currentPlayer?.player_id,
          button_position: gameState.button_position,
          this_player_id: playerId
        });
      }
      
      if (actionRequest) {
        console.log("Action request details:", {
          request_player_id: actionRequest.player_id,
          options: actionRequest.options,
          timestamp: actionRequest.timestamp
        });
      }
    }
    
    // Basic validation first
    if (!gameState || !playerId || !actionRequest) {
      if (process.env.NODE_ENV !== "production") {
        console.log("isPlayerTurn returning false because:", 
                  !gameState ? "no gameState" : 
                  !playerId ? "no playerId" : 
                  "no actionRequest");
      }
      return false;
    }
    
    // Determine if it's this player's turn by actionRequest or by gameState index
    let result = actionRequest.player_id === playerId;
    if (!result && gameState && typeof gameState.current_player_idx === 'number' && gameState.current_player_idx >= 0) {
        const turnPlayer = gameState.players[gameState.current_player_idx];
        result = turnPlayer?.player_id === playerId;
    }
    
    if (process.env.NODE_ENV !== "production") {
      console.log("isPlayerTurn check - actionRequest.player_id:", actionRequest.player_id, 
                "playerId:", playerId, 
                "result:", result);
                
      // If this should be the player's turn but result is false, log a warning
      if (!result && gameState.current_player_idx >= 0) {
        const currentPlayer = gameState.players[gameState.current_player_idx];
        if (currentPlayer && currentPlayer.player_id === playerId) {
          console.warn("❗ TURN MISMATCH: Game state indicates it's this player's turn, but actionRequest is for different player!");
          console.warn("This might indicate an issue with action request handling.");
        }
      }
    }
    
    // Debug final decision
    if (process.env.NODE_ENV !== "production") {
        console.log("isPlayerTurn final result:", result, {
            playerId,
            "actionRequest.player_id": actionRequest.player_id,
            "gameState.current_player_idx": gameState?.current_player_idx
        });
    }
    return result;
  }, [gameState, playerId, actionRequest]);
  
  // Clear action request when it's no longer the player's turn
  useEffect(() => {
    if (actionRequest && lastAction && actionRequest.player_id === lastAction.player_id) {
      setActionRequest(null);
    }
  }, [lastAction, actionRequest]);
  
  // Method to get and log connection health statistics
  const getConnectionHealth = useCallback(() => {
    const metrics = getConnectionMetrics();
    console.log('WebSocket Connection Health Report:');
    console.log(`- Status: ${status}`);
    console.log(`- Connection stability: ${(metrics.connectionStability * 100).toFixed(0)}%`);
    console.log(`- Total connections: ${metrics.connectionCount}`);
    console.log(`- Disconnections: ${metrics.disconnectionCount}`);
    console.log(`- Successful reconnects: ${metrics.successfulReconnects}`);
    console.log(`- Failed reconnects: ${metrics.failedReconnects}`);
    console.log(`- Average reconnect time: ${Math.round(metrics.averageReconnectTime)}ms`);
    
    // Special handling for extended metrics
    const extendedMetrics = metrics as any;
    
    if (extendedMetrics.currentConnectionDuration !== undefined) {
      console.log(`- Current connection duration: ${Math.round(extendedMetrics.currentConnectionDuration / 1000)}s`);
    }
    
    if (extendedMetrics.uptimePercentage !== undefined) {
      console.log(`- Estimated uptime: ${extendedMetrics.uptimePercentage.toFixed(1)}%`);
    }
    return metrics;
  }, [status, getConnectionMetrics]);

  return {
    status,
    gameState,
    lastAction,
    actionRequest,
    handResult,
    chatMessages,
    actionLog,
    errors,
    sendAction,
    sendChat,
    reconnect,
    isPlayerTurn,
    lastMessage,
    getConnectionHealth,
    // Turn highlighting states
    currentTurnPlayerId,
    showTurnHighlight,
    processingAITurn,
    foldedPlayerId
  };
};