import React, { useState } from 'react';
import {
  Container,
  Paper,
  TextField,
  Button,
  Typography,
  Alert,
  CircularProgress,
} from '@mui/material';

export default function Login({ onLogin }) {
  const [githubToken, setGithubToken] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Store the GitHub token directly
      localStorage.setItem('access_token', githubToken);

      // Test the token with a metrics request
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/metrics/generate`,
        {
          headers: {
            Authorization: `Bearer ${githubToken}`,
          },
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        // If token is invalid, clear it from storage
        localStorage.removeItem('access_token');
        throw new Error(errorData.detail || 'Invalid GitHub token');
      }

      // If we get here, token is valid
      onLogin(githubToken);
    } catch (err) {
      setError(err.message);
      localStorage.removeItem('access_token');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="sm" sx={{ mt: 8 }}>
      <Paper sx={{ p: 4 }}>
        <Typography variant="h4" align="center" gutterBottom>
          DoraPulse Login
        </Typography>

        <Typography variant="body1" align="center" sx={{ mb: 3 }}>
          Enter your GitHub token to continue
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          <TextField
            fullWidth
            label="GitHub Token"
            type="password"
            value={githubToken}
            onChange={(e) => setGithubToken(e.target.value)}
            required
            sx={{ mb: 3 }}
          />

          <Button
            fullWidth
            type="submit"
            variant="contained"
            disabled={loading}
            sx={{ mb: 2 }}
          >
            {loading ? <CircularProgress size={24} /> : 'Login'}
          </Button>
        </form>

        <Typography variant="body2" color="text.secondary" align="center">
          To get a GitHub token, go to GitHub Settings → Developer settings →
          Personal access tokens
        </Typography>
      </Paper>
    </Container>
  );
}
