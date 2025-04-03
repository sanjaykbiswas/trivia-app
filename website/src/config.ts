// website/src/config.ts
// --- START OF FILE ---
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'; // Fallback includes /api

// Add a check to see if the environment variable was loaded
if (!import.meta.env.VITE_API_BASE_URL) {
  console.warn(
    "VITE_API_BASE_URL environment variable not found. " +
    `Using default value: ${API_BASE_URL}. ` +
    "Make sure you have a .env.development file with VITE_API_BASE_URL=http://<your_backend_ip>:<your_backend_port>/api"
  );
} else {
  console.log("Using API Base URL from environment:", API_BASE_URL);
}


export { API_BASE_URL };
// --- END OF FILE ---