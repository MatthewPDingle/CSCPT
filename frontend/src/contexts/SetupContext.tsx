import React, { createContext, useContext, useState, ReactNode, useRef } from 'react';

// Player archetype types
export type Archetype = 'TAG' | 'LAG' | 'TightPassive' | 'CallingStation' | 'Maniac' | 'Beginner' | 'Unpredictable';

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
      
      // Migrate from Random to Unpredictable if needed
      if (parsedConfig.tournament.archetypeDistribution.Random !== undefined) {
        parsedConfig.tournament.archetypeDistribution.Unpredictable = 
          parsedConfig.tournament.archetypeDistribution.Random;
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
        const originalDistribution = { ...prevConfig.tournament.archetypeDistribution };
        const newPercentage = Math.round(percentage);
        const oldValue = originalDistribution[archetype];
        
        if (newPercentage === oldValue || newPercentage < 0 || newPercentage > 100) {
          return prevConfig;
        }
        
        const delta = newPercentage - oldValue;
        const newDistribution = { ...originalDistribution };
        newDistribution[archetype] = newPercentage;
        
        const otherArchetypes = Object.keys(originalDistribution).filter(
          key => key !== archetype
        ) as Archetype[];
        
        const totalOther = otherArchetypes.reduce(
          (sum, key) => sum + originalDistribution[key], 
          0
        );
        
        if (totalOther > 0) {
          otherArchetypes.forEach(key => {
            const proportion = originalDistribution[key] / totalOther;
            const adjustedValue = originalDistribution[key] - (proportion * delta);
            newDistribution[key] = adjustedValue;
          });
        } else if (otherArchetypes.length > 0) {
          if (newPercentage < 100) {
            newDistribution[otherArchetypes[0]] = 100 - newPercentage;
          }
        }
        
        Object.keys(newDistribution).forEach(key => {
          newDistribution[key as Archetype] = Math.round(newDistribution[key as Archetype]);
        });
        
        const total = Object.values(newDistribution).reduce((sum, val) => sum + val, 0);
        if (total !== 100) {
          const difference = 100 - total;
          const adjustableArchetypes = otherArchetypes.filter(key => newDistribution[key] > 0);
          
          if (adjustableArchetypes.length > 0) {
            const maxArchetype = adjustableArchetypes.reduce((max, key) => 
              newDistribution[key] > newDistribution[max] ? key : max, 
              adjustableArchetypes[0]);
            newDistribution[maxArchetype] += difference;
          } else if (newDistribution[archetype] + difference <= 100 && newDistribution[archetype] + difference >= 0) {
            newDistribution[archetype] += difference;
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