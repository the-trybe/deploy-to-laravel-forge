# Express Hello World API

A simple Express.js API with a hello-world route for testing GitHub Actions.

## Features

- Simple REST API built with Express.js
- Hello World endpoint at `/api/hello`
- Health check endpoint at `/health`
- JSON responses

## Endpoints

### GET /api/hello

Returns a hello world message with timestamp.

**Response:**

```json
{
  "message": "Hello World!",
  "timestamp": "2025-11-02T...",
  "success": true
}
```

### GET /health

Health check endpoint.

**Response:**

```json
{
  "status": "healthy",
  "uptime": 123.456,
  "timestamp": "2025-11-02T..."
}
```

### GET /

Root endpoint listing all available endpoints.

## Installation

Install dependencies:

```bash
npm install
```

## Running the Application

Start the server:

```bash
npm start
```

Or for development:

```bash
npm run dev
```

The server will start on `http://localhost:3000` by default.

## Environment Variables

- `PORT` - Server port (default: 3000)

## Testing

You can test the API using curl:

```bash
# Test hello world endpoint
curl http://localhost:3000/api/hello

# Test health check
curl http://localhost:3000/health
```

## Project Structure

```
express/
├── index.js          # Main application file
├── package.json      # Project dependencies and scripts
├── .gitignore       # Git ignore rules
└── README.md        # This file
```
