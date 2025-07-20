import React, { useEffect, useState } from 'react';
import { Typography, Box, Paper, Grid, CircularProgress } from '@mui/material';
import axios from 'axios';

function Dashboard() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        console.log('API URL:', import.meta.env.VITE_API_URL);
        console.log(
          'GitHub Token:',
          import.meta.env.VITE_GITHUB_TOKEN ? 'Token exists' : 'No token found'
        );

        const response = await axios.get(
          `${import.meta.env.VITE_API_URL}/metrics/generate`,
          {
            headers: {
              Authorization: `Bearer ${import.meta.env.VITE_GITHUB_TOKEN}`,
              'Content-Type': 'application/json',
              Accept: 'application/json',
            },
            params: {
              repo: import.meta.env.VITE_GITHUB_REPO,
            },
          }
        );
        console.log('Response:', response.data);
        setMetrics(response.data);
        setLoading(false);
      } catch (err) {
        console.error('Error details:', err);
        if (err.response) {
          // The request was made and the server responded with a status code
          // that falls out of the range of 2xx
          console.error('Response data:', err.response.data);
          console.error('Response status:', err.response.status);
          console.error('Response headers:', err.response.headers);
          setError(`${err.message}: ${JSON.stringify(err.response.data)}`);
        } else if (err.request) {
          // The request was made but no response was received
          console.error('Request error:', err.request);
          setError('No response received from server');
        } else {
          // Something happened in setting up the request that triggered an Error
          console.error('Error message:', err.message);
          setError(err.message);
        }
        setLoading(false);
      }
    };

    fetchMetrics();
  }, []);

  if (loading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="80vh"
      >
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ mt: 4 }}>
        <Typography color="error" variant="h6">
          Error loading metrics: {error}
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ mt: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        DORA Metrics Dashboard
      </Typography>

      <Grid container spacing={3}>
        {metrics &&
          Object.entries(metrics).map(([key, value]) => (
            <Grid item xs={12} md={6} key={key}>
              <Paper elevation={3} sx={{ p: 3 }}>
                <Typography variant="h6" gutterBottom>
                  {key
                    .split('_')
                    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
                    .join(' ')}
                </Typography>
                <Typography variant="h4">
                  {typeof value === 'number' ? value.toFixed(2) : value}
                </Typography>
              </Paper>
            </Grid>
          ))}
      </Grid>
    </Box>
  );
}

export default Dashboard;
