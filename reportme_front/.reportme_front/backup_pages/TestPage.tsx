import React from 'react';
import { Typography, Box } from '@mui/material';

const TestPage: React.FC = () => {
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4">Test Page</Typography>
      <Typography>Se você está vendo isso, o React está funcionando!</Typography>
    </Box>
  );
};

export default TestPage;
