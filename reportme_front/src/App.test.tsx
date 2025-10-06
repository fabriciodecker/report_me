import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';

test('renders test page', () => {
  render(<App />);
  const testElement = screen.getByText('✅ Frontend funcionando!');
  expect(testElement).toBeInTheDocument();
});
