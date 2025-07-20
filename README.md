# DoraPulse

A Developer Productivity and DORA Metrics Dashboard that analyzes GitHub repositories to calculate and display DORA (DevOps Research and Assessment) metrics.

## Features

- Real-time DORA metrics calculation
- GitHub repository analysis
- Interactive dashboard
- Configurable repository selection

## Understanding DORA Metrics

DoraPulse calculates the four key metrics defined by the DORA (DevOps Research and Assessment) team:

1. **Deployment Frequency**

   - How often an organization successfully releases to production
   - Elite performers: Multiple deployments per day
   - Metric shows: Release cadence and batch size

2. **Lead Time for Changes**

   - Time taken from code commit to code running in production
   - Elite performers: Less than one hour
   - Metric shows: Process efficiency and deployment pipeline health

3. **Mean Time to Recovery (MTTR)**

   - How long it takes to restore service after an incident
   - Elite performers: Less than one hour
   - Metric shows: Incident response effectiveness

4. **Change Failure Rate**
   - Percentage of changes that lead to degraded service
   - Elite performers: 0-15%
   - Metric shows: Quality of testing and review processes

### References

- [Official DORA Research Program](https://www.devops-research.com/research.html)
- [Google Cloud's DORA Metrics](https://cloud.google.com/blog/products/devops-sre/using-the-four-keys-to-measure-your-devops-performance)
- [DORA's State of DevOps Reports](https://www.devops-research.com/research.html#reports)
- [DORA Metrics in GitHub](https://resources.github.com/devops/tools/dora-metrics/)
- [Accelerate: The Science of Lean Software](https://books.google.com/books?id=Kax-DwAAQBAJ) - The book that introduced DORA metrics

### Performance Categories

Below are the performance categories for each metric according to DORA research:

| Metric                | Elite     | High              | Medium              | Low            |
| --------------------- | --------- | ----------------- | ------------------- | -------------- |
| Deployment Frequency  | On-demand | Weekly to monthly | Monthly to yearly   | Yearly or less |
| Lead Time for Changes | < 1 hour  | 1 day to 1 week   | 1 month to 6 months | > 6 months     |
| MTTR                  | < 1 hour  | < 1 day           | < 1 week            | > 1 week       |
| Change Failure Rate   | 0-15%     | 16-30%            | 31-45%              | > 45%          |

## Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- Poetry (Python dependency management)
- npm (Node.js package manager)
- GitHub Personal Access Token with following scopes:
  - `repo` (full repository access)
  - `read:user`
  - `read:org`

## Project Structure

```
DoraPulse/
├── backend/         # FastAPI backend
│   ├── auth/       # Authentication handling
│   ├── common/     # Shared utilities
│   └── metrics/    # DORA metrics calculation
└── frontend/       # React + Vite frontend
    ├── src/        # Source code
    └── public/     # Static assets
```

## Quick Start

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/chandanrattan/DoraPulse.git
cd DoraPulse
```

### 2. Backend Setup

1. Navigate to backend directory:

   ```bash
   cd backend
   ```

2. Install Poetry (if not already installed):

   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. Install dependencies:
   ```bash
   poetry install
   ```

### 3. Frontend Setup

1. Navigate to frontend directory:

   ```bash
   cd frontend
   ```

2. Install dependencies:

   ```bash
   npm install
   ```

3. Set up environment variables:
   ```bash
   cp .env.template .env
   ```
   Then edit `.env` file and add your:
   - GitHub Personal Access Token
   - Target repository name

## Running the Application

### 1. Start the Backend

```bash
cd backend
poetry run uvicorn main:app --reload
```

The backend will be available at http://127.0.0.1:8000

### 2. Start the Frontend

In a new terminal:

```bash
cd frontend
npm run dev
```

The frontend will be available at http://localhost:5173

## Environment Variables

### Frontend (.env file)

```plaintext
# API URL (default for local development)
VITE_API_URL=http://127.0.0.1:8000

# Your GitHub Personal Access Token
VITE_GITHUB_TOKEN=your_github_token_here

# Repository to analyze (format: owner/repo)
VITE_GITHUB_REPO=owner/repository
```

## Troubleshooting

### Common Issues

1. **All Metrics Show 0**

   - Verify your GitHub token has required permissions
   - Check if the repository exists and has pull requests
   - Look for error messages in browser console (F12)
   - Verify the repository name format is correct (owner/repo)

2. **Cannot Connect to Backend**

   - Ensure backend is running (http://127.0.0.1:8000)
   - Check VITE_API_URL in frontend .env file
   - Look for CORS errors in browser console

3. **GitHub API Errors**

   - Verify token permissions include 'repo' access
   - Check if you've hit API rate limits
   - Verify repository name is correct

   ```bash
   cd backend
   poetry install
   ```

4. Create `.env` file:

   ```bash
   cp .env.example .env
   # Edit .env with your GitHub token and repository details
   ```

5. Run the server:
   ```bash
   poetry run uvicorn main:app --reload
   ```

### Frontend Setup

1. Install Node.js:

   - Download Node.js LTS version from [nodejs.org](https://nodejs.org/)
   - Run the installer and follow the installation steps
   - Verify installation by running:

     ```bash
     node --version
     npm --version
     ```

2. Install dependencies:

   ```bash
   cd frontend
   npm install
   ```

3. Create `.env` file:

   ```bash
   cp .env.example .env
   # Set VITE_API_URL=http://localhost:8000
   ```

4. Run the development server:

   ```bash
   npm run dev
   ```

   The frontend will be available at [http://localhost:5173](http://localhost:5173)

## Running the Application

1. Start the Backend:

   ```bash
   cd backend
   poetry run uvicorn main:app --reload
   ```

   The backend API will be available at [http://localhost:8000](http://localhost:8000)

2. Start the Frontend (in a new terminal):

   ```bash
   cd frontend
   npm run dev
   ```

3. Access the Application:
   - Open [http://localhost:5173](http://localhost:5173) in your browser
   - Login using your GitHub Personal Access Token (PAT)
   - The dashboard will display your DORA metrics

## Environment Setup

### Backend Environment Variables (.env)

```env
GITHUB_TOKEN=your_github_token_here
GITHUB_REPO=owner/repository_name
```

### Frontend Environment Variables (.env)

```env
VITE_API_URL=http://localhost:8000
```

## Troubleshooting

### Backend Issues

- Ensure Poetry is installed and in your PATH
- Verify GitHub token has correct permissions (needs `repo` scope)
- Check backend logs for detailed error messages
- Ensure all dependencies are installed with `poetry install`
- Verify `.env` file exists with correct values

### Frontend Issues

- Ensure Node.js and npm are installed correctly
- Clear browser cache and localStorage:
  1. Open browser DevTools (F12)
  2. Go to Application → Storage → Clear Site Data
- Verify the API URL in frontend `.env` file
- Check browser console for error messages
- If needed, reinstall dependencies:

  ```bash
  rm -rf node_modules
  npm install
  ```

### Authentication Issues

1. GitHub Token Problems:

   - Ensure token has required permissions (needs `repo` scope)
   - Token should be valid and not expired
   - Verify token works by testing in GitHub API

2. API Connection Issues:

   - Confirm backend is running (`http://localhost:8000`)
   - Check frontend `.env` has correct API URL
   - Verify no CORS issues in browser console

3. Session Issues:
   - Clear browser localStorage
   - Log out and log in again
   - Ensure token is being stored correctly

### Common Errors and Solutions

1. "Could not validate credentials":

   - Check GitHub token permissions
   - Verify token is not expired
   - Ensure token is correctly set in backend `.env`

2. "Cannot connect to API":

   - Verify backend server is running
   - Check correct ports are being used
   - Ensure no firewall blocking

3. "Module not found":
   - Run `npm install` in frontend directory
   - Check `package.json` for correct dependencies
   - Verify node_modules directory exists

## Troubleshooting

1. Backend Issues:

   - Ensure Poetry is installed and in your PATH
   - Verify GitHub token has correct permissions
   - Check backend logs for detailed error messages
   - Ensure all dependencies are installed: `poetry install`

2. Frontend Issues:

   - Ensure Node.js and npm are installed
   - Clear browser cache and localStorage
   - Verify API URL in frontend .env file
   - Check browser console for error messages
   - Reinstall dependencies if needed: `rm -rf node_modules && npm install`

3. Authentication Issues:

   - Ensure GitHub token has required permissions
   - Check if backend is running and accessible
   - Verify the correct API URL in frontend .env
   - Try clearing browser localStorage

4. Common Error Solutions:
   - "Could not validate credentials": Check GitHub token and permissions
   - "Cannot connect to API": Verify backend is running
   - "Module not found": Run `npm install` in frontend directory
