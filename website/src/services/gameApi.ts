// website/src/services/gameApi.ts
// --- START OF FULL MODIFIED FILE ---
import { API_BASE_URL } from '@/config';
import {
    ApiGameSessionResponse,
    GameCreationPayload,
    ApiGameJoinRequest,
    ApiParticipantListResponse,
    ApiGameStartResponse,
    ApiGamePlayQuestionListResponse,
    // --- ADDED IMPORTS ---
    ApiGameSubmitAnswerRequest,
    ApiQuestionResultResponse
} from '@/types/apiTypes';

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
  url.searchParams.append('user_id', userId);

  console.log("Attempting to create game with URL:", url.toString());
  console.log("Payload:", payload);

  try {
    const response = await fetch(url.toString(), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    console.log("API Response Status (Create):", response.status);
    const responseData = await response.json();
    console.log("API Response Data (Create):", responseData);

    if (!response.ok) {
      const errorDetail = responseData?.detail || response.statusText || `HTTP error ${response.status}`;
      console.error("API Error Detail (Create):", errorDetail);
      throw new Error(`Failed to create game: ${errorDetail}`);
    }

    if (!responseData || typeof responseData.id !== 'string' || typeof responseData.code !== 'string') {
        console.error("Invalid response structure received (Create):", responseData);
        throw new Error("Received invalid game session data from server.");
    }

    return responseData as ApiGameSessionResponse;

  } catch (error) {
    console.error("Error creating game session:", error);
    throw error;
  }
};

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
    const responseData = await response.json();
    console.log("API Response Data (Join):", responseData);

    if (!response.ok) {
      const errorDetail = responseData?.detail || response.statusText || `HTTP error ${response.status}`;
       console.error("API Error Detail (Join):", errorDetail);
       let userFriendlyError = `Failed to join game: ${errorDetail}`;
        if (response.status === 404 || (typeof errorDetail === 'string' && errorDetail.toLowerCase().includes("not found"))) {
            userFriendlyError = "Game code not found. Please double-check the code.";
        } else if (response.status === 400) {
             if (errorDetail && typeof errorDetail === 'string') {
                 if (errorDetail.toLowerCase().includes("not accepting new players")) {
                    userFriendlyError = "This game has already started or is no longer accepting players.";
                 } else if (errorDetail.toLowerCase().includes("is full")) {
                    userFriendlyError = "This game is full.";
                 } else {
                    userFriendlyError = `Failed to join: ${errorDetail}`;
                 }
             } else {
                 userFriendlyError = "Could not join the game. Please check the code and try again.";
             }
        }
      throw new Error(userFriendlyError);
    }

    if (!responseData || typeof responseData.id !== 'string' || typeof responseData.code !== 'string') {
        console.error("Invalid response structure received (Join):", responseData);
        throw new Error("Received invalid game session data from server after joining.");
    }

    return responseData as ApiGameSessionResponse;

  } catch (error) {
    console.error("Error joining game session:", error);
    throw error;
  }
};

/**
 * Fetches the list of participants for a given game session.
 * @param gameId - The ID of the game session.
 * @returns A promise resolving to the participant list response.
 * @throws If the API request fails.
 */
export const getGameParticipants = async (gameId: string): Promise<ApiParticipantListResponse> => {
  // Validate gameId format slightly before sending
  if (!gameId || typeof gameId !== 'string' || gameId.length < 5) { // Basic check
      console.error("Invalid gameId provided to getGameParticipants:", gameId);
      throw new Error("Invalid game ID provided.");
  }
  const url = `${API_BASE_URL}/games/${gameId}/participants`;
  console.log("Fetching participants for game:", gameId, "URL:", url);

  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
    });

    console.log("API Response Status (Get Participants):", response.status);
    const responseData = await response.json();
    // console.log("API Response Data (Get Participants):", responseData); // Verbose logging

    if (!response.ok) {
      const errorDetail = responseData?.detail || response.statusText || `HTTP error ${response.status}`;
      console.error("API Error Detail (Get Participants):", errorDetail);
      throw new Error(`Failed to fetch participants: ${errorDetail}`);
    }

    if (!responseData || typeof responseData.total !== 'number' || !Array.isArray(responseData.participants)) {
        console.error("Invalid participant list structure received:", responseData);
        throw new Error("Received invalid participant data from server.");
    }

    return responseData as ApiParticipantListResponse;

  } catch (error) {
    console.error("Error fetching participants:", error);
    throw error;
  }
};

/**
 * Starts the game session (called by the host).
 * @param gameId - The ID of the game session to start.
 * @param hostUserId - The ID of the user initiating the start (must be the host).
 * @returns A promise resolving to the game start response, including the first question.
 * @throws If the API request fails (e.g., user not host, game not found, wrong status).
 */
export const startGame = async (gameId: string, hostUserId: string): Promise<ApiGameStartResponse> => {
    if (!gameId || !hostUserId) {
      throw new Error("Game ID and Host User ID are required to start the game.");
    }
    const url = new URL(`${API_BASE_URL}/games/${gameId}/start`);
    url.searchParams.append('user_id', hostUserId);

    console.log("Attempting to start game:", gameId, "by host:", hostUserId, "URL:", url.toString());

    try {
        const response = await fetch(url.toString(), {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
            },
        });

        console.log("API Response Status (Start Game):", response.status);
        const responseData = await response.json();
        // console.log("API Response Data (Start Game):", responseData); // Verbose logging

        if (!response.ok) {
            const errorDetail = responseData?.detail || response.statusText || `HTTP error ${response.status}`;
            console.error("API Error Detail (Start Game):", errorDetail);
            throw new Error(`Failed to start game: ${errorDetail}`);
        }

        if (!responseData || typeof responseData.status !== 'string' || !responseData.current_question || typeof responseData.current_question.index !== 'number') {
            console.error("Invalid game start response structure received:", responseData);
            throw new Error("Received invalid game start data from server.");
        }

        return responseData as ApiGameStartResponse;

    } catch (error) {
        console.error("Error starting game:", error);
        throw error;
    }
};

/**
 * Fetches the actual questions prepared for a specific game session.
 * @param gameId - The ID of the game session.
 * @returns A promise resolving to the list of questions for gameplay.
 * @throws If the API request fails.
 */
export const getGamePlayQuestions = async (gameId: string): Promise<ApiGamePlayQuestionListResponse> => {
    if (!gameId || typeof gameId !== 'string' || gameId.length < 5) {
      console.error("Invalid gameId provided to getGamePlayQuestions:", gameId);
      throw new Error("Invalid game ID provided.");
    }
    const url = `${API_BASE_URL}/games/${gameId}/play-questions`;
    console.log("Fetching gameplay questions for game:", gameId, "URL:", url);

    try {
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
            },
        });

        console.log("API Response Status (Get Play Questions):", response.status);
        const responseData = await response.json();
        // console.log("API Response Data (Get Play Questions):", responseData); // Verbose logging

        if (!response.ok) {
            const errorDetail = responseData?.detail || response.statusText || `HTTP error ${response.status}`;
            console.error("API Error Detail (Get Play Questions):", errorDetail);
            throw new Error(`Failed to fetch gameplay questions: ${errorDetail}`);
        }

        // --- UPDATED VALIDATION ---
        if (!responseData || typeof responseData.game_id !== 'string' || !Array.isArray(responseData.questions) || typeof responseData.total_questions !== 'number') {
            console.error("Invalid gameplay questions response structure:", responseData);
            throw new Error("Received invalid gameplay questions data from server.");
        }
        // Add check for correct_answer_id in the first question if available
        if (responseData.questions.length > 0 && typeof responseData.questions[0].correct_answer_id !== 'string') {
            console.error("Invalid question structure within gameplay questions response (missing correct_answer_id):", responseData.questions[0]);
            throw new Error("Received invalid question data (missing correct ID) from server.");
        }
        // --- END UPDATED VALIDATION ---

        return responseData as ApiGamePlayQuestionListResponse;

    } catch (error) {
        console.error("Error fetching gameplay questions:", error);
        throw error;
    }
};

// --- *** ADDED FUNCTION *** ---
/**
 * Submits a player's answer for a specific question in a game session.
 * @param gameId - The ID of the game session.
 * @param participantId - The ID of the participant submitting the answer.
 * @param payload - The answer data (question index and the answer itself).
 * @returns A promise resolving to the result of the submission (correctness, scores).
 * @throws If the API request fails.
 */
export const submitAnswer = async (
    gameId: string,
    participantId: string,
    payload: ApiGameSubmitAnswerRequest
): Promise<ApiQuestionResultResponse> => {
    if (!gameId || !participantId) {
        throw new Error("Game ID and Participant ID are required to submit an answer.");
    }
    const url = new URL(`${API_BASE_URL}/games/${gameId}/submit`);
    url.searchParams.append('participant_id', participantId);

    console.log("Attempting to submit answer:", payload, "to URL:", url.toString());

    try {
        const response = await fetch(url.toString(), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            body: JSON.stringify(payload),
        });

        console.log("API Response Status (Submit Answer):", response.status);
        const responseData = await response.json();
        // console.log("API Response Data (Submit Answer):", responseData); // Verbose logging

        if (!response.ok) {
            const errorDetail = responseData?.detail || response.statusText || `HTTP error ${response.status}`;
            console.error("API Error Detail (Submit Answer):", errorDetail);
            throw new Error(`Failed to submit answer: ${errorDetail}`);
        }

        // Validate response structure
        if (responseData === null || typeof responseData !== 'object' || typeof responseData.is_correct !== 'boolean' || typeof responseData.correct_answer !== 'string' || typeof responseData.score !== 'number' || typeof responseData.total_score !== 'number') {
           console.error("Invalid answer result structure received:", responseData);
           throw new Error("Received invalid answer result data from server.");
        }


        return responseData as ApiQuestionResultResponse;

    } catch (error) {
        console.error("Error submitting answer:", error);
        throw error;
    }
};
// --- *** END ADDED FUNCTION *** ---

// --- END OF FILE ---