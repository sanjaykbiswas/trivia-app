// website/src/services/gameApi.ts
import { API_BASE_URL } from '@/config';
import { ApiGameSessionResponse, GameCreationPayload } from '@/types/apiTypes'; // We'll define these types next

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

    console.log("API Response Status:", response.status);

    // Attempt to parse JSON regardless of status for more detailed error
    let responseData: any;
    try {
      responseData = await response.json();
      console.log("API Response Data:", responseData);
    } catch (jsonError) {
      console.error("Failed to parse JSON response:", jsonError);
      // If JSON parsing fails, throw error based on status only
      if (!response.ok) {
         throw new Error(`HTTP error ${response.status}: Failed to create game. Invalid response format.`);
      }
      // If response was ok but JSON failed (unlikely for FastAPI), rethrow
       throw new Error(`Failed to parse successful response JSON: ${jsonError}`);
    }


    if (!response.ok) {
      // Use detail from FastAPI error if available, otherwise status text
      const errorDetail = responseData?.detail || response.statusText || `HTTP error ${response.status}`;
      console.error("API Error Detail:", errorDetail);
      throw new Error(`Failed to create game: ${errorDetail}`);
    }

    // Validate the structure matches ApiGameSessionResponse (basic check)
    if (!responseData || typeof responseData.id !== 'string' || typeof responseData.code !== 'string') {
        console.error("Invalid response structure received:", responseData);
        throw new Error("Received invalid game session data from server.");
    }

    return responseData as ApiGameSessionResponse;

  } catch (error) {
    console.error("Error creating game session:", error);
    // Re-throw the error to be caught by the calling component
    throw error;
  }
};

// Add other game-related API functions here (joinGame, startGame, submitAnswer, etc.)