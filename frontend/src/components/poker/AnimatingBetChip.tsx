import React, { useEffect, useRef } from 'react';
import styled, { keyframes } from 'styled-components';

interface AnimatingBetChipProps {
  amount: number;
  fromPosition: { x: string; y: string };
  targetPosition: { x: string; y: string };
  onEnd: () => void;
}

// Keyframes to move chip from start to target and fade out
const moveAnim = (
  sx: string,
  sy: string,
  tx: string,
  ty: string
) => keyframes`
  0% {
    left: ${sx};
    top: ${sy};
    transform: translate(-50%, -50%) scale(1);
    opacity: 1;
  }
  99% {
    left: ${tx};
    top: ${ty};
    transform: translate(-50%, -50%) scale(0.5);
    opacity: 1;
  }
  100% {
    left: ${tx};
    top: ${ty};
    transform: translate(-50%, -50%) scale(0.5);
    opacity: 0;
  }
`;

// Chip element styled with absolute positioning and animation
const Chip = styled.div<{
  sx: string;
  sy: string;
  tx: string;
  ty: string;
}>
  `
  position: absolute;
  background-color: #ffd700;
  color: #000;
  padding: 4px 8px;
  border-radius: 8px;
  font-size: 0.75rem;
  font-weight: bold;
  box-shadow: 0 2px 4px rgba(0,0,0,0.4);
  z-index: 50;
  animation: ${({ sx, sy, tx, ty }) => moveAnim(sx, sy, tx, ty)} 0.5s ease-in-out forwards;
`;

const AnimatingBetChip: React.FC<AnimatingBetChipProps> = ({
  amount,
  fromPosition,
  targetPosition,
  onEnd,
}) => {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (el) {
      el.addEventListener('animationend', onEnd);
      return () => el.removeEventListener('animationend', onEnd);
    }
  }, [onEnd]);

  if (!fromPosition) return null;
  return (
    <Chip
      ref={ref}
      sx={fromPosition.x}
      sy={fromPosition.y}
      tx={targetPosition.x}
      ty={targetPosition.y}
    >
      ${amount}
    </Chip>
  );
};

export default AnimatingBetChip;