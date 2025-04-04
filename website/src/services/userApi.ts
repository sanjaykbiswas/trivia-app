// website/src/services/userApi.ts
// --- START OF FULL MODIFIED FILE ---
import { API_BASE_URL } from '@/config';
import { ApiUserCreateRequest, ApiUserResponse } from '@/types/apiTypes';

// --- Keep existing createUser and createTemporaryUser functions ---
export const createUser = async (payload: ApiUserCreateRequest): Promise<ApiUserResponse> => {
  const url = `${API_BASE_URL}/users/`; // <<< ADDED SLASH
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
      const errorDetail = responseData?.detail || response.statusText || `HTTP error ${response.status}`;
       let formattedError = errorDetail;
       if (Array.isArray(errorDetail)) {
         formattedError = errorDetail.map(err => `${err.loc?.join('.')} - ${err.msg}`).join('; ');
       } else if (typeof errorDetail === 'object') {
         formattedError = JSON.stringify(errorDetail);
       }
      console.error("API Error Detail (Create User):", formattedError);
      throw new Error(`Failed to create user: ${formattedError}`);
    }

    if (!responseData || typeof responseData.id !== 'string') {
        console.error("Invalid user response structure received:", responseData);
        throw new Error("Received invalid user data from server.");
    }

    return responseData as ApiUserResponse;

  } catch (error) {
    console.error("Error creating user:", error);
    throw error;
  }
};

export const createTemporaryUser = async (displayName?: string | null): Promise<ApiUserResponse> => {
    // Allow null to be passed
    const payload: ApiUserCreateRequest = {
        is_temporary: true,
        displayname: displayName, // Pass null if provided as null
    };
    return createUser(payload);
};


// --- *** ADD THIS NEW FUNCTION *** ---
/**
 * Updates an existing user on the backend.
 * @param userId - The ID of the user to update.
 * @param payload - Data containing the fields to update.
 * @returns The updated user data from the backend.
 * @throws If the API request fails.
 */
export const updateUser = async (userId: string, payload: Partial<ApiUserCreateRequest>): Promise<ApiUserResponse> => {
    const url = `${API_BASE_URL}/users/${userId}`; // PUT /api/users/{user_id}
    console.log(`Attempting to update user ${userId}:`, payload);

    try {
        const response = await fetch(url, {
            method: 'PUT', // Use PUT for updates
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            body: JSON.stringify(payload),
        });

        console.log(`API Response Status (Update User ${userId}):`, response.status);

        let responseData: any;
         try {
             responseData = await response.json();
             console.log(`API Response Data (Update User ${userId}):`, responseData);
         } catch (jsonError) {
             console.error(`Failed to parse JSON response (Update User ${userId}):`, jsonError);
             if (!response.ok) {
                 throw new Error(`HTTP error ${response.status}: Failed to update user. Invalid response format.`);
             }
             throw new Error(`Failed to parse successful response JSON (Update User ${userId}): ${jsonError}`);
         }


        if (!response.ok) {
            const errorDetail = responseData?.detail || response.statusText || `HTTP error ${response.status}`;
            let formattedError = errorDetail;
            if (Array.isArray(errorDetail)) {
              formattedError = errorDetail.map(err => `${err.loc?.join('.')} - ${err.msg}`).join('; ');
            } else if (typeof errorDetail === 'object') {
              formattedError = JSON.stringify(errorDetail);
            }
            console.error(`API Error Detail (Update User ${userId}):`, formattedError);
            throw new Error(`Failed to update user: ${formattedError}`);
        }

        if (!responseData || typeof responseData.id !== 'string') {
            console.error("Invalid user response structure received after update:", responseData);
            throw new Error("Received invalid user data from server after update.");
        }

        return responseData as ApiUserResponse;

    } catch (error) {
        console.error(`Error updating user ${userId}:`, error);
        throw error; // Re-throw
    }
};
// --- *** END ADDED FUNCTION *** ---
// --- END OF FILE ---