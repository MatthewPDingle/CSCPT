import React from 'react';
import styled, { css, keyframes } from 'styled-components';

interface CardProps {
  card: string | null;
  faceDown?: boolean;
  isCommunity?: boolean;
  /** Pulse animation when this card wins */
  flash?: boolean;
}

// Animation duration
const CARD_REVEAL_DURATION = 300;  // ms reveal animation
// Reveal keyframes
const cardReveal = keyframes`
  from { transform: scale(0.8); opacity: 0; }
  to   { transform: scale(1);   opacity: 1; }
`;
const CardContainer = styled.div<{ $faceDown: boolean; $isCommunity: boolean; $flash?: boolean }>`
  width: ${props => props.$isCommunity ? '80px' : '70px'};
  height: ${props => props.$isCommunity ? '115px' : '100px'};
  border-radius: 8px;
  background-color: white;
  box-shadow: ${props => props.$isCommunity ? 
    '0 3px 15px rgba(0, 0, 0, 0.4), 0 0 10px rgba(255, 255, 255, 0.3)' : 
    '0 2px 8px rgba(0, 0, 0, 0.3)'};
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  user-select: none;
  font-weight: bold;
  transition: transform 0.3s ease;
  
  &:hover {
    transform: translateY(-5px);
  }
  
  ${props => props.$faceDown && `
    background: linear-gradient(135deg, #6d4c41 25%, #8d6e63 25%, #8d6e63 50%, #6d4c41 50%, #6d4c41 75%, #8d6e63 75%);
    background-size: 20px 20px;
    color: transparent;
    
    &:after {
      content: "";
      position: absolute;
      top: 5px;
      left: 5px;
      right: 5px;
      bottom: 5px;
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 5px;
    }
  `}
  
  ${props => props.$isCommunity && !props.$faceDown && `
    animation: pulse 1.5s infinite alternate;
    
    @keyframes pulse {
      from { box-shadow: 0 3px 15px rgba(0, 0, 0, 0.4), 0 0 5px rgba(255, 255, 255, 0.3); }
      to { box-shadow: 0 3px 15px rgba(0, 0, 0, 0.4), 0 0 15px rgba(255, 255, 255, 0.7); }
    }
  `}
  /* Flash animation for winning cards */
  ${props => props.$flash && css`
    animation: potFlash 0.6s ease-out;
  `}
  /* Reveal animation when card is face up */
  ${props => !props.$faceDown && css`
    animation: ${cardReveal} ${CARD_REVEAL_DURATION}ms ease-out;
  `}
`;

const CardValue = styled.div<{ color: string; $isCommunity: boolean }>`
  position: absolute;
  top: 5px;
  left: 5px;
  font-size: ${props => props.$isCommunity ? '1.4rem' : '1.2rem'};
  color: ${props => props.color};
  font-weight: bold;
  text-shadow: ${props => props.$isCommunity ? '0 1px 2px rgba(0, 0, 0, 0.2)' : 'none'};
`;

const CardSymbol = styled.div<{ color: string; $isCommunity: boolean }>`
  font-size: ${props => props.$isCommunity ? '2.5rem' : '2rem'};
  color: ${props => props.color};
  text-shadow: ${props => props.$isCommunity ? '0 1px 3px rgba(0, 0, 0, 0.2)' : 'none'};
`;

const EmptyCard = styled.div<{ $isCommunity: boolean }>`
  width: ${props => props.$isCommunity ? '80px' : '70px'};
  height: ${props => props.$isCommunity ? '115px' : '100px'};
  border-radius: 8px;
  border: 2px dashed rgba(255, 255, 255, 0.4);
  background-color: rgba(255, 255, 255, 0.05);
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

const Card: React.FC<CardProps> = ({ card, faceDown = false, isCommunity = false, flash = false }) => {
  if (!card) {
    return <EmptyCard $isCommunity={!!isCommunity} />;
  }
  
  const { value, suit, color } = parseCard(card);
  
  return (
    <CardContainer $faceDown={!!faceDown} $isCommunity={!!isCommunity} $flash={!!flash}>
      <CardValue color={color} $isCommunity={!!isCommunity}>{value}</CardValue>
      <CardSymbol color={color} $isCommunity={!!isCommunity}>{suit}</CardSymbol>
    </CardContainer>
  );
};

export default Card;