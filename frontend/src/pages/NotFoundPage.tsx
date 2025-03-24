import React from 'react';
import { Link } from 'react-router-dom';
import styled from 'styled-components';

const NotFoundContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
  text-align: center;
  padding: 0 2rem;
`;

const ErrorCode = styled.h1`
  font-size: 6rem;
  margin: 0;
  color: #e74c3c;
`;

const ErrorMessage = styled.h2`
  font-size: 1.5rem;
  margin-bottom: 2rem;
  color: #2c3e50;
`;

const HomeLink = styled(Link)`
  color: #3498db;
  text-decoration: none;
  font-size: 1.1rem;
  
  &:hover {
    text-decoration: underline;
  }
`;

const NotFoundPage: React.FC = () => {
  return (
    <NotFoundContainer>
      <ErrorCode>404</ErrorCode>
      <ErrorMessage>Page Not Found</ErrorMessage>
      <HomeLink to="/">Return to Home</HomeLink>
    </NotFoundContainer>
  );
};

export default NotFoundPage;