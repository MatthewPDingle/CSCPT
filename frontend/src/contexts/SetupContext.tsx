import React, { createContext, useContext, useState, ReactNode } from 'react';

// Player archetype types
export type Archetype = 'TAG' | 'LAG' | 'TightPassive' | 'CallingStation' | 'Maniac' | 'Beginner' | 'Unpredictable';

// Game mode types
export type GameMode = 'cash' | 'tournament';

// Tournament tier types
export type TournamentTier = 'Local' | 'Regional' | 'National' | 'International';

// Tournament stage types
export type TournamentStage = 'Early' | 'Mid' | 'MoneyBubble' | 'PostBubble' | 'FinalTable';

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
  Maniac: number;
  Beginner: number;
  Unpredictable: number;
}

// Main game configuration state
export interface GameConfig {
  gameMode: GameMode;
  
  // Cash game specific settings
  cashGame: {
    buyIn: number;
    smallBlind: number;
    bigBlind: number;
    ante: number;
    tableSize: number;
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
    TAG: 3,
    LAG: 15,
    TightPassive: 2,
    CallingStation: 10,
    Maniac: 15,
    Beginner: 45,
    Unpredictable: 10
  },
  Regional: {
    TAG: 10,
    LAG: 20,
    TightPassive: 15,
    CallingStation: 10,
    Maniac: 15,
    Beginner: 20,
    Unpredictable: 10
  },
  National: {
    TAG: 25,
    LAG: 25,
    TightPassive: 20,
    CallingStation: 5,
    Maniac: 10,
    Beginner: 5,
    Unpredictable: 10
  },
  International: {
    TAG: 40,
    LAG: 30,
    TightPassive: 15,
    CallingStation: 2,
    Maniac: 3,
    Beginner: 0,
    Unpredictable: 10
  }
};

// Generate default players for cash game
const generateDefaultPlayers = (tableSize: number): PlayerConfig[] => {
  const archetypes: Archetype[] = ['TAG', 'LAG', 'TightPassive', 'CallingStation', 'Maniac', 'Beginner', 'Unpredictable'];
  
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
    smallBlind: 5,
    bigBlind: 10,
    ante: 0,
    tableSize: 6,
    players: generateDefaultPlayers(6)
  },
  tournament: {
    tier: 'Local',
    stage: 'Early',
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
      
      // Migrate from Random to Unpredictable if needed
      if (parsedConfig.tournament.archetypeDistribution.Random !== undefined) {
        // Copy Random value to Unpredictable
        parsedConfig.tournament.archetypeDistribution.Unpredictable = 
          parsedConfig.tournament.archetypeDistribution.Random;
        
        // Delete the old Random property
        delete parsedConfig.tournament.archetypeDistribution.Random;
      }
      
      // Migrate cash game players from Random to Unpredictable
      if (parsedConfig.cashGame && parsedConfig.cashGame.players) {
        parsedConfig.cashGame.players.forEach((player: PlayerConfig) => {
          if (player.archetype === 'Random' as any) {
            player.archetype = 'Unpredictable';
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

      // If table size changes, regenerate players
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
      // If tier changes, update the default distribution
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
        cashGame: {
          ...prevConfig.cashGame,
          players
        }
      };
      
      localStorage.setItem('gameSetup', JSON.stringify(newConfig));
      return newConfig;
    });
  };

  // Update tournament archetype distribution
  const updateArchetypeDistribution = (archetype: Archetype, percentage: number) => {
    setConfig(prevConfig => {
      // Create a copy of the current distribution
      const newDistribution = { ...prevConfig.tournament.archetypeDistribution };
      
      // Ensure percentage is an integer
      const newPercentage = Math.round(percentage);
      
      // Get the current value of the changed archetype
      const oldValue = newDistribution[archetype];
      
      // If no change or percentage is invalid, return existing config
      if (newPercentage === oldValue || newPercentage < 0 || newPercentage > 100) {
        return prevConfig;
      }
      
      // Calculate the delta (change in value)
      const delta = newPercentage - oldValue;
      
      // Set the new value for the changed archetype
      newDistribution[archetype] = newPercentage;
      
      // Get other archetypes (excluding the one being changed)
      const otherArchetypes = Object.keys(newDistribution).filter(
        key => key !== archetype
      ) as Archetype[];
      
      // Calculate the sum of all other archetype values
      const totalOther = otherArchetypes.reduce(
        (sum, key) => sum + newDistribution[key], 
        0
      );
      
      // If there are other archetypes with non-zero values, distribute the delta
      if (totalOther > 0) {
        // Store original values before adjustment
        const originalValues: Record<Archetype, number> = {} as Record<Archetype, number>;
        otherArchetypes.forEach(key => {
          originalValues[key] = newDistribution[key];
        });
        
        // Distribute the negative of the delta proportionally among other archetypes
        otherArchetypes.forEach(key => {
          // Calculate the proportion of this archetype relative to the total of others
          const proportion = originalValues[key] / totalOther;
          // Apply the proportional adjustment: new_value = old_value - (old_value / total_other) * delta
          newDistribution[key] = Math.max(0, originalValues[key] - (proportion * delta));
        });
      } else if (newPercentage < 100 && otherArchetypes.length > 0) {
        // If all other archetypes are 0, assign the remainder to the first one
        newDistribution[otherArchetypes[0]] = 100 - newPercentage;
      }
      
      // Round values to integers
      otherArchetypes.forEach(key => {
        newDistribution[key] = Math.round(newDistribution[key]);
      });
      
      // Final check to ensure total is exactly 100
      const total = Object.values(newDistribution).reduce((sum, val) => sum + val, 0);
      if (total !== 100) {
        const difference = 100 - total;
        
        // Find archetypes that can be adjusted (not the one just changed)
        const adjustableArchetypes = otherArchetypes.filter(key => newDistribution[key] > 0);
        
        if (adjustableArchetypes.length > 0) {
          // Find the largest value
          const maxArchetype = adjustableArchetypes.reduce((max, key) => 
            newDistribution[key] > newDistribution[max] ? key : max, 
            adjustableArchetypes[0]);
            
          // Apply the adjustment to the largest value
          newDistribution[maxArchetype] += difference;
        } else if (newPercentage + difference <= 100 && newPercentage + difference >= 0) {
          // If no other archetypes can be adjusted, modify the changed one
          newDistribution[archetype] += difference;
        }
      }
      
      const newConfig = {
        ...prevConfig,
        tournament: {
          ...prevConfig.tournament,
          archetypeDistribution: newDistribution
        }
      };
      
      localStorage.setItem('gameSetup', JSON.stringify(newConfig));
      return newConfig;
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
        tournament: {
          ...prevConfig.tournament,
          archetypeDistribution: defaultDistributions[tier]
        }
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