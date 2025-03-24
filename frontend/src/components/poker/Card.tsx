import React from 'react';
import styled from 'styled-components';

interface CardProps {
  card: string | null;
  faceDown?: boolean;
}

const CardContainer = styled.div<{ faceDown: boolean }>`
  width: 70px;
  height: 100px;
  border-radius: 5px;
  background-color: white;
  box-shadow: 0 1px 5px rgba(0, 0, 0, 0.2);
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  user-select: none;
  font-weight: bold;
  ${props => props.faceDown && `
    background: linear-gradient(135deg, #6d4c41 25%, #8d6e63 25%, #8d6e63 50%, #6d4c41 50%, #6d4c41 75%, #8d6e63 75%);
    background-size: 20px 20px;
    color: transparent;
  `}
`;

const CardValue = styled.div<{ color: string }>`
  position: absolute;
  top: 5px;
  left: 5px;
  font-size: 1.2rem;
  color: ${props => props.color};
`;

const CardSymbol = styled.div<{ color: string }>`
  font-size: 2rem;
  color: ${props => props.color};
`;

const EmptyCard = styled.div`
  width: 70px;
  height: 100px;
  border-radius: 5px;
  border: 2px dashed rgba(255, 255, 255, 0.3);
`;

// Helper function to parse card string
const parseCard = (cardString: string) => {
  if (!cardString || cardString.length < 2) {
    return { value: '?', suit: '?', color: 'black' };
  }
  
  const value = cardString.slice(0, -1);
  const suit = cardString.slice(-1);
  
  let displayValue = value;
  if (value === 'T') displayValue = '10';
  if (value === 'J') displayValue = 'J';
  if (value === 'Q') displayValue = 'Q';
  if (value === 'K') displayValue = 'K';
  if (value === 'A') displayValue = 'A';
  
  let suitSymbol = '♠';
  let color = 'black';
  
  switch (suit.toLowerCase()) {
    case 'h':
      suitSymbol = '♥';
      color = 'red';
      break;
    case 'd':
      suitSymbol = '♦';
      color = 'red';
      break;
    case 'c':
      suitSymbol = '♣';
      color = 'black';
      break;
    case 's':
    default:
      suitSymbol = '♠';
      color = 'black';
  }
  
  return { value: displayValue, suit: suitSymbol, color };
};

const Card: React.FC<CardProps> = ({ card, faceDown = false }) => {
  if (!card) {
    return <EmptyCard />;
  }
  
  const { value, suit, color } = parseCard(card);
  
  return (
    <CardContainer faceDown={faceDown}>
      <CardValue color={color}>{value}</CardValue>
      <CardSymbol color={color}>{suit}</CardSymbol>
    </CardContainer>
  );
};

export default Card;