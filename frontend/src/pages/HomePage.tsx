import React from 'react';
import { Link } from 'react-router-dom';
import styled from 'styled-components';

const HomeContainer = styled.div`
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
  text-align: center;
`;

const Title = styled.h1`
  color: #2c3e50;
  font-size: 2.5rem;
  margin-bottom: 1.5rem;
`;

const Subtitle = styled.p`
  color: #34495e;
  font-size: 1.2rem;
  margin-bottom: 2rem;
`;

const StartGameButton = styled(Link)`
  display: inline-block;
  background-color: #3498db;
  color: white;
  padding: 1rem 2rem;
  font-size: 1.2rem;
  text-decoration: none;
  border-radius: 4px;
  transition: background-color 0.3s;

  &:hover {
    background-color: #2980b9;
  }
`;

const HomePage: React.FC = () => {
  return (
    <HomeContainer>
      <Title>Chip Swinger Championship Poker Trainer</Title>
      <Subtitle>
        Practice your poker skills against AI opponents with different play styles.
        Improve your game and get real-time feedback on your decisions.
      </Subtitle>
      <StartGameButton to="/game">Start Game</StartGameButton>
    </HomeContainer>
  );
};

export default HomePage;