const express = require("express");

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware to parse JSON
app.use(express.json());

// Hello World route
app.get("/api/hello", (req, res) => {
  res.json({
    message: "Hello World!",
    timestamp: new Date().toISOString(),
    success: true,
  });
});

// Health check route
app.get("/health", (req, res) => {
  res.json({
    status: "healthy",
    uptime: process.uptime(),
    timestamp: new Date().toISOString(),
  });
});

// Root route
app.get("/", (req, res) => {
  res.json({
    message: "Express Hello World API",
    endpoints: {
      hello: "/api/hello",
      health: "/health",
    },
  });
});

// Start server
app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
  console.log(
    `Try the hello-world endpoint: http://localhost:${PORT}/api/hello`
  );
});
