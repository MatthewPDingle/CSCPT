import React from 'react';
import { useSetup } from '../../../contexts/SetupContext';
import CashGamePlayerSetup from './CashGamePlayerSetup';
import TournamentPlayerSetup from './TournamentPlayerSetup';

const PlayerSetup: React.FC = () => {
  const { config } = useSetup();
  
  // Render the appropriate setup component based on game mode
  return config.gameMode === 'cash' 
    ? <CashGamePlayerSetup /> 
    : <TournamentPlayerSetup />;
};

export default PlayerSetup;