// website/src/services/gameApi.ts
// --- START OF FILE ---
import { API_BASE_URL } from '@/config';
// Import all needed types for this file
import { ApiGameSessionResponse, GameCreationPayload, ApiGameJoinRequest } from '@/types/apiTypes';

/**
 * Creates a new game session on the backend.
 * @param payload - Data required to create the game (packId, settings).
 * @param userId - The ID of the user creating the game (host).
 * @returns The created game session data from the backend.
 * @throws If the API request fails.
 */
export const createGameSession = async (
  payload: GameCreationPayload,
  userId: string // Passed as query parameter
): Promise<ApiGameSessionResponse> => {
  const url = new URL(`${API_BASE_URL}/games/create`);
  url.searchParams.append('user_id', userId); // Add user_id as query param

  console.log("Attempting to create game with URL:", url.toString());
  console.log("Payload:", payload);

  try {
    const response = await fetch(url.toString(), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json', // Explicitly accept JSON
      },
      body: JSON.stringify(payload),
    });

    console.log("API Response Status (Create):", response.status);

    let responseData: any;
    try {
      responseData = await response.json();
      console.log("API Response Data (Create):", responseData);
    } catch (jsonError) {
      console.error("Failed to parse JSON response (Create):", jsonError);
      if (!response.ok) {
         throw new Error(`HTTP error ${response.status}: Failed to create game. Invalid response format.`);
      }
       throw new Error(`Failed to parse successful response JSON (Create): ${jsonError}`);
    }


    if (!response.ok) {
      const errorDetail = responseData?.detail || response.statusText || `HTTP error ${response.status}`;
      console.error("API Error Detail (Create):", errorDetail);
      throw new Error(`Failed to create game: ${errorDetail}`);
    }

    // Validate the structure matches ApiGameSessionResponse (basic check)
    if (!responseData || typeof responseData.id !== 'string' || typeof responseData.code !== 'string') {
        console.error("Invalid response structure received (Create):", responseData);
        throw new Error("Received invalid game session data from server.");
    }

    return responseData as ApiGameSessionResponse;

  } catch (error) {
    console.error("Error creating game session:", error);
    throw error; // Re-throw
  }
};


// --- THIS IS THE MISSING FUNCTION ---
/**
 * Joins an existing game session.
 * @param payload - Data required to join (game_code, display_name).
 * @param userId - The ID of the user joining the game.
 * @returns The game session data after joining.
 * @throws If the API request fails or the game cannot be joined.
 */
export const joinGameSession = async (
  payload: ApiGameJoinRequest,
  userId: string
): Promise<ApiGameSessionResponse> => {
  const url = new URL(`${API_BASE_URL}/games/join`);
  url.searchParams.append('user_id', userId);

  console.log("Attempting to join game with URL:", url.toString());
  console.log("Join Payload:", payload);

  try {
    const response = await fetch(url.toString(), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    console.log("API Response Status (Join):", response.status);

    let responseData: any;
     try {
      responseData = await response.json();
      console.log("API Response Data (Join):", responseData);
    } catch (jsonError) {
      console.error("Failed to parse JSON response (Join):", jsonError);
      if (!response.ok) {
         // Provide more context if possible based on status code
         let errorMsg = `HTTP error ${response.status}: Failed to join game. Invalid response format.`;
          if (response.status === 404) errorMsg = `HTTP error ${response.status}: Game code not found.`;
          if (response.status === 400) errorMsg = `HTTP error ${response.status}: Invalid request (e.g., game full, already started, bad code format).`;
         throw new Error(errorMsg);
      }
       throw new Error(`Failed to parse successful response JSON (Join): ${jsonError}`);
    }


    if (!response.ok) {
      // Use detail from FastAPI error if available, otherwise status text
      const errorDetail = responseData?.detail || response.statusText || `HTTP error ${response.status}`;
       console.error("API Error Detail (Join):", errorDetail);
       // Enhance error message for common join issues
        let userFriendlyError = `Failed to join game: ${errorDetail}`;
        if (response.status === 404) {
            userFriendlyError = "Game code not found. Please double-check the code.";
        } else if (response.status === 400) {
             if (errorDetail && typeof errorDetail === 'string') {
                 if (errorDetail.toLowerCase().includes("game not found")) {
                    userFriendlyError = "Game code not found. Please double-check the code.";
                 } else if (errorDetail.toLowerCase().includes("not accepting new players")) {
                    userFriendlyError = "This game has already started or is no longer accepting players.";
                 } else if (errorDetail.toLowerCase().includes("is full")) {
                    userFriendlyError = "This game is full.";
                 } else {
                    userFriendlyError = `Failed to join: ${errorDetail}`; // Use backend message if specific
                 }
             } else {
                 userFriendlyError = "Could not join the game. Please check the code and try again.";
             }
        }
      throw new Error(userFriendlyError);
    }

     // Validate the structure matches ApiGameSessionResponse
    if (!responseData || typeof responseData.id !== 'string' || typeof responseData.code !== 'string') {
        console.error("Invalid response structure received (Join):", responseData);
        throw new Error("Received invalid game session data from server after joining.");
    }

    return responseData as ApiGameSessionResponse;

  } catch (error) {
    console.error("Error joining game session:", error);
    throw error; // Re-throw
  }
};
// --- END MISSING FUNCTION ---


// Add other game-related API functions here (startGame, submitAnswer, etc.)
// --- END OF FILE ---