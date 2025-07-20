import React from 'react';
import { Box, Container } from '@mui/material';
import Dashboard from './pages/Dashboard';

function App() {
  return (
    <Container maxWidth="lg">
      <Box sx={{ mt: 4 }}>
        <Dashboard />
      </Box>
    </Container>
  );
}

export default App;
