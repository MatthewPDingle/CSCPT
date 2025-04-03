import React, { createContext, useContext, useState, ReactNode, useRef } from 'react';

// Player archetype types
export type Archetype = 'TAG' | 'LAG' | 'TightPassive' | 'CallingStation' | 'LoosePassive' | 'Maniac' | 'Beginner' | 'Adaptable' | 'GTO' | 'ShortStack' | 'Trappy';

// Game mode types
export type GameMode = 'cash' | 'tournament';

// Tournament tier types
export type TournamentTier = 'Local' | 'Regional' | 'National' | 'International';

// Tournament stage types
export type TournamentStage = 'Beginning' | 'Mid' | 'Money Bubble' | 'Post Bubble' | 'Final Table';

// Ante value type
export type AnteValueType = 'SB' | 'BB' | '2xBB';

// Individual player configuration (for cash games)
export interface PlayerConfig {
  position: number;
  archetype: Archetype;
  name: string;
}

// Archetype distribution configuration (for tournaments)
export interface ArchetypeDistribution {
  TAG: number;
  LAG: number;
  TightPassive: number;
  CallingStation: number;
  LoosePassive: number;
  Maniac: number;
  Beginner: number;
  Adaptable: number;
  GTO: number;
  ShortStack: number;
  Trappy: number;
}

// Betting structure type
export type BettingStructure = 'no_limit' | 'pot_limit' | 'fixed_limit';

// Main game configuration state
export interface GameConfig {
  gameMode: GameMode;
  
  // Cash game specific settings
  cashGame: {
    buyIn: number;
    minBuyIn: number;
    maxBuyIn: number;
    smallBlind: number;
    bigBlind: number;
    ante: number;
    tableSize: number;
    bettingStructure: BettingStructure;
    rakePercentage: number;
    rakeCap: number;
    players: PlayerConfig[];
  };
  
  // Tournament specific settings
  tournament: {
    tier: TournamentTier;
    stage: TournamentStage;
    payoutStructure: string;
    buyInAmount: number;
    levelDuration: number;
    startingChips: number;
    totalPlayers: number;
    startingBigBlind: number;
    startingSmallBlind: number;
    anteEnabled: boolean;
    anteStartLevel: number;
    anteValueType: AnteValueType;
    rebuyOption: boolean;
    rebuyLevelCutoff: number;
    archetypeDistribution: ArchetypeDistribution;
  };
}

// Default archetype distributions by tournament tier
const defaultDistributions: Record<TournamentTier, ArchetypeDistribution> = {
  Local: {
    TAG: 5,
    LAG: 10,
    TightPassive: 5,
    CallingStation: 15,
    LoosePassive: 15,
    Maniac: 10,
    Beginner: 25,
    Adaptable: 3,
    GTO: 2,
    ShortStack: 5,
    Trappy: 5
  },
  Regional: {
    TAG: 15,
    LAG: 15,
    TightPassive: 10,
    CallingStation: 10,
    LoosePassive: 8,
    Maniac: 8,
    Beginner: 12,
    Adaptable: 6,
    GTO: 5,
    ShortStack: 6,
    Trappy: 5
  },
  National: {
    TAG: 20,
    LAG: 18,
    TightPassive: 8,
    CallingStation: 5,
    LoosePassive: 4,
    Maniac: 5,
    Beginner: 5,
    Adaptable: 12,
    GTO: 12,
    ShortStack: 6,
    Trappy: 5
  },
  International: {
    TAG: 23,
    LAG: 18,
    TightPassive: 3,
    CallingStation: 2,
    LoosePassive: 2,
    Maniac: 2,
    Beginner: 3,
    Adaptable: 16,
    GTO: 20,
    ShortStack: 6,
    Trappy: 5
  }
};

// Generate default players for cash game
const generateDefaultPlayers = (tableSize: number): PlayerConfig[] => {
  const archetypes: Archetype[] = [
    'TAG', 'LAG', 'TightPassive', 'CallingStation', 'LoosePassive', 
    'Maniac', 'Beginner', 'Adaptable', 'GTO', 'ShortStack', 'Trappy'
  ];
  
  return Array.from({ length: tableSize - 1 }, (_, index) => ({
    position: index + 1,
    archetype: archetypes[index % archetypes.length],
    name: `Player ${index + 1}`
  }));
};

// Default configuration
const defaultConfig: GameConfig = {
  gameMode: 'cash',
  cashGame: {
    buyIn: 1000,
    minBuyIn: 400,   // 40 BBs
    maxBuyIn: 2000,  // 200 BBs
    smallBlind: 5,
    bigBlind: 10,
    ante: 0,
    tableSize: 6,
    bettingStructure: 'no_limit',
    rakePercentage: 0.05,
    rakeCap: 5,
    players: generateDefaultPlayers(6)
  },
  tournament: {
    tier: 'Local',
    stage: 'Beginning',
    payoutStructure: 'Standard',
    buyInAmount: 100,
    levelDuration: 15,
    startingChips: 50000,
    totalPlayers: 50,
    startingBigBlind: 100,
    startingSmallBlind: 50,
    anteEnabled: false,
    anteStartLevel: 3,
    anteValueType: 'BB',
    rebuyOption: true,
    rebuyLevelCutoff: 5,
    archetypeDistribution: defaultDistributions.Local
  }
};

// Context type
interface SetupContextType {
  config: GameConfig;
  setGameMode: (mode: GameMode) => void;
  setCashGameOption: <K extends keyof GameConfig['cashGame']>(
    key: K, 
    value: GameConfig['cashGame'][K]
  ) => void;
  setTournamentOption: <K extends keyof GameConfig['tournament']>(
    key: K, 
    value: GameConfig['tournament'][K]
  ) => void;
  updateCashGamePlayer: (position: number, data: Partial<PlayerConfig>) => void;
  updateArchetypeDistribution: (archetype: Archetype, percentage: number) => void;
  resetToDefault: () => void;
  resetTournamentDistribution: () => void;
}

// Create context
export const SetupContext = createContext<SetupContextType | undefined>(undefined);

// Provider props
interface SetupProviderProps {
  children: ReactNode;
}

// Context provider
export const SetupProvider: React.FC<SetupProviderProps> = ({ children }) => {
  const [config, setConfig] = useState<GameConfig>(() => {
    // Load from localStorage if available
    const savedConfig = localStorage.getItem('gameSetup');

    if (savedConfig) {
      // Parse saved config
      const parsedConfig = JSON.parse(savedConfig);
      
      // Migrate from Random/Unpredictable to Adaptable if needed
      if (parsedConfig.tournament.archetypeDistribution.Random !== undefined) {
        parsedConfig.tournament.archetypeDistribution.Adaptable = 
          parsedConfig.tournament.archetypeDistribution.Random;
        delete parsedConfig.tournament.archetypeDistribution.Random;
      }
      if (parsedConfig.tournament.archetypeDistribution.Unpredictable !== undefined) {
        parsedConfig.tournament.archetypeDistribution.Adaptable = 
          (parsedConfig.tournament.archetypeDistribution.Adaptable || 0) + 
          parsedConfig.tournament.archetypeDistribution.Unpredictable;
        delete parsedConfig.tournament.archetypeDistribution.Unpredictable;
      }
      
      // Add missing archetypes with zero values
      const allArchetypes: Archetype[] = ['TAG', 'LAG', 'TightPassive', 'CallingStation', 
        'LoosePassive', 'Maniac', 'Beginner', 'Adaptable', 'GTO', 'ShortStack', 'Trappy'];
      
      allArchetypes.forEach(archetype => {
        if (parsedConfig.tournament.archetypeDistribution[archetype] === undefined) {
          parsedConfig.tournament.archetypeDistribution[archetype] = 0;
        }
      });
      
      // Migrate cash game players from Random/Unpredictable to Adaptable
      if (parsedConfig.cashGame && parsedConfig.cashGame.players) {
        parsedConfig.cashGame.players.forEach((player: PlayerConfig) => {
          if (player.archetype === 'Random' as any || player.archetype === 'Unpredictable' as any) {
            player.archetype = 'Adaptable';
          }
        });
      }
      
      return parsedConfig;
    }
    
    return defaultConfig;
  });

  // Set game mode
  const setGameMode = (mode: GameMode) => {
    setConfig(prevConfig => {
      const newConfig = { ...prevConfig, gameMode: mode };
      localStorage.setItem('gameSetup', JSON.stringify(newConfig));
      return newConfig;
    });
  };

  // Update cash game option
  const setCashGameOption = <K extends keyof GameConfig['cashGame']>(
    key: K, 
    value: GameConfig['cashGame'][K]
  ) => {
    setConfig(prevConfig => {
      const newCashGame = { ...prevConfig.cashGame, [key]: value };
      if (key === 'tableSize' && typeof value === 'number') {
        newCashGame.players = generateDefaultPlayers(value as number);
      }
      const newConfig = { ...prevConfig, cashGame: newCashGame };
      localStorage.setItem('gameSetup', JSON.stringify(newConfig));
      return newConfig;
    });
  };

  // Update tournament option
  const setTournamentOption = <K extends keyof GameConfig['tournament']>(
    key: K, 
    value: GameConfig['tournament'][K]
  ) => {
    setConfig(prevConfig => {
      if (key === 'tier' && typeof value === 'string') {
        const tier = value as TournamentTier;
        const newTournament = { 
          ...prevConfig.tournament, 
          [key]: value,
          archetypeDistribution: defaultDistributions[tier]
        };
        const newConfig = { ...prevConfig, tournament: newTournament };
        localStorage.setItem('gameSetup', JSON.stringify(newConfig));
        return newConfig;
      } else {
        const newTournament = { ...prevConfig.tournament, [key]: value };
        const newConfig = { ...prevConfig, tournament: newTournament };
        localStorage.setItem('gameSetup', JSON.stringify(newConfig));
        return newConfig;
      }
    });
  };

  // Update cash game player
  const updateCashGamePlayer = (position: number, data: Partial<PlayerConfig>) => {
    setConfig(prevConfig => {
      const players = [...prevConfig.cashGame.players];
      const playerIndex = players.findIndex(p => p.position === position);
      if (playerIndex !== -1) {
        players[playerIndex] = { ...players[playerIndex], ...data };
      }
      const newConfig = {
        ...prevConfig,
        cashGame: { ...prevConfig.cashGame, players }
      };
      localStorage.setItem('gameSetup', JSON.stringify(newConfig));
      return newConfig;
    });
  };

  // Use a ref to prevent recursive updates
  const isUpdatingDistribution = useRef(false);

  // Update tournament archetype distribution
  const updateArchetypeDistribution = (archetype: Archetype, percentage: number) => {
    if (isUpdatingDistribution.current) return;
    isUpdatingDistribution.current = true;
    
    setConfig(prevConfig => {
      try {
        // Ensure all archetypes are present in the distribution
        const allArchetypes: Archetype[] = [
          'TAG', 'LAG', 'TightPassive', 'CallingStation', 'LoosePassive', 
          'Maniac', 'Beginner', 'Adaptable', 'GTO', 'ShortStack', 'Trappy'
        ];
        
        // Create a complete distribution with all archetypes
        const originalDistribution = { ...prevConfig.tournament.archetypeDistribution };
        
        // Add any missing archetypes with 0 value
        allArchetypes.forEach(arch => {
          if (originalDistribution[arch] === undefined) {
            originalDistribution[arch] = 0;
          }
        });
        
        const newPercentage = Math.round(percentage);
        const oldValue = originalDistribution[archetype];
        
        if (newPercentage === oldValue || newPercentage < 0 || newPercentage > 100) {
          return prevConfig;
        }
        
        const delta = newPercentage - oldValue;
        const newDistribution = { ...originalDistribution };
        newDistribution[archetype] = newPercentage;
        
        // Make sure we consider ALL archetypes
        const otherArchetypes = allArchetypes.filter(key => key !== archetype);
        
        const totalOther = otherArchetypes.reduce(
          (sum, key) => sum + (originalDistribution[key] || 0), 
          0
        );
        
        if (totalOther > 0) {
          otherArchetypes.forEach(key => {
            // Use 0 as default if key doesn't exist
            const currentValue = originalDistribution[key] || 0;
            const proportion = currentValue / totalOther;
            const adjustedValue = currentValue - (proportion * delta);
            newDistribution[key] = adjustedValue;
          });
        } else if (otherArchetypes.length > 0) {
          if (newPercentage < 100) {
            // Distribute remainder evenly among other archetypes
            const remainder = 100 - newPercentage;
            const perArchetype = remainder / otherArchetypes.length;
            otherArchetypes.forEach(key => {
              newDistribution[key] = perArchetype;
            });
          }
        }
        
        // Round all values to integers
        Object.keys(newDistribution).forEach(key => {
          newDistribution[key as Archetype] = Math.round(newDistribution[key as Archetype]);
        });
        
        // Ensure total is exactly 100%
        const total = Object.values(newDistribution).reduce((sum, val) => sum + val, 0);
        if (total !== 100) {
          const difference = 100 - total;
          
          // First try to adjust archetypes with non-zero values
          const adjustableArchetypes = otherArchetypes.filter(key => newDistribution[key] > 0);
          
          if (adjustableArchetypes.length > 0) {
            // Find the archetype with the largest value to adjust
            const maxArchetype = adjustableArchetypes.reduce((max, key) => 
              newDistribution[key] > newDistribution[max] ? key : max, 
              adjustableArchetypes[0]);
            
            // Make sure the adjustment doesn't make the value negative
            if (newDistribution[maxArchetype] + difference >= 0) {
              newDistribution[maxArchetype] += difference;
            } else {
              // Distribute the difference across all adjustable archetypes
              const perArchetype = Math.ceil(Math.abs(difference) / adjustableArchetypes.length);
              
              // Try to distribute evenly
              for (const key of adjustableArchetypes) {
                if (newDistribution[key] >= perArchetype) {
                  newDistribution[key] -= perArchetype;
                  break;
                }
              }
            }
          } else if (newDistribution[archetype] + difference <= 100 && newDistribution[archetype] + difference >= 0) {
            // If no other archetypes have values, adjust the current one
            newDistribution[archetype] += difference;
          } else {
            // Last resort: set one of the other archetypes to abs(difference)
            if (difference < 0) {
              // We need to subtract from the total - give value to the first archetype
              newDistribution[otherArchetypes[0]] = Math.abs(difference);
            }
          }
        }
        
        Object.keys(newDistribution).forEach(key => {
          newDistribution[key as Archetype] = Math.max(0, Math.min(100, newDistribution[key as Archetype]));
        });
        
        const newConfig = {
          ...prevConfig,
          tournament: { ...prevConfig.tournament, archetypeDistribution: newDistribution }
        };
        
        localStorage.setItem('gameSetup', JSON.stringify(newConfig));
        return newConfig;
      } finally {
        setTimeout(() => { isUpdatingDistribution.current = false; }, 0);
      }
    });
  };

  // Reset to default configuration
  const resetToDefault = () => {
    setConfig(defaultConfig);
    localStorage.setItem('gameSetup', JSON.stringify(defaultConfig));
  };

  // Reset tournament distribution to default based on current tier
  const resetTournamentDistribution = () => {
    setConfig(prevConfig => {
      const tier = prevConfig.tournament.tier;
      const newConfig = {
        ...prevConfig,
        tournament: { ...prevConfig.tournament, archetypeDistribution: defaultDistributions[tier] }
      };
      localStorage.setItem('gameSetup', JSON.stringify(newConfig));
      return newConfig;
    });
  };

  return (
    <SetupContext.Provider value={{
      config,
      setGameMode,
      setCashGameOption,
      setTournamentOption,
      updateCashGamePlayer,
      updateArchetypeDistribution,
      resetToDefault,
      resetTournamentDistribution
    }}>
      {children}
    </SetupContext.Provider>
  );
};

// Custom hook to use the setup context
export const useSetup = () => {
  const context = useContext(SetupContext);
  if (context === undefined) {
    throw new Error('useSetup must be used within a SetupProvider');
  }
  return context;
};