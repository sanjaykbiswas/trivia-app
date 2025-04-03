// website/src/services/userApi.ts
// --- START OF FILE ---
import { API_BASE_URL } from '@/config';
import { ApiUserCreateRequest, ApiUserResponse } from '@/types/apiTypes';

/**
 * Creates a new user on the backend.
 * @param payload - Data for the new user.
 * @returns The created user data from the backend.
 * @throws If the API request fails.
 */
export const createUser = async (payload: ApiUserCreateRequest): Promise<ApiUserResponse> => {
  const url = `${API_BASE_URL}/users`; // POST /api/users
  console.log("Attempting to create user:", payload);

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    console.log("API Response Status (Create User):", response.status);

    let responseData: any;
    try {
        responseData = await response.json();
        console.log("API Response Data (Create User):", responseData);
    } catch (jsonError) {
        console.error("Failed to parse JSON response (Create User):", jsonError);
        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}: Failed to create user. Invalid response format.`);
        }
        throw new Error(`Failed to parse successful response JSON (Create User): ${jsonError}`);
    }

    if (!response.ok) {
      // Use detail from FastAPI error if available (like validation errors)
      const errorDetail = responseData?.detail || response.statusText || `HTTP error ${response.status}`;
       // Handle potential array structure for validation errors
       let formattedError = errorDetail;
       if (Array.isArray(errorDetail)) {
         formattedError = errorDetail.map(err => `${err.loc?.join('.')} - ${err.msg}`).join('; ');
       } else if (typeof errorDetail === 'object') {
         formattedError = JSON.stringify(errorDetail); // Basic stringify if it's an object
       }
      console.error("API Error Detail (Create User):", formattedError);
      throw new Error(`Failed to create user: ${formattedError}`);
    }

    // Basic validation
    if (!responseData || typeof responseData.id !== 'string') {
        console.error("Invalid user response structure received:", responseData);
        throw new Error("Received invalid user data from server.");
    }

    return responseData as ApiUserResponse;

  } catch (error) {
    console.error("Error creating user:", error);
    throw error; // Re-throw
  }
};

/**
 * Helper function specifically for creating a temporary user.
 * @param displayName Optional display name for the temporary user.
 * @returns The created temporary user data.
 */
export const createTemporaryUser = async (displayName?: string): Promise<ApiUserResponse> => {
    const payload: ApiUserCreateRequest = {
        is_temporary: true,
        displayname: displayName || null, // Use null if no name provided
    };
    return createUser(payload);
};
// --- END OF FILE ---