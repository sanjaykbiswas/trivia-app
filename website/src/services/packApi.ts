// website/src/services/packApi.ts
// --- START OF FILE ---
import { API_BASE_URL } from '@/config';
import { ApiPackListResponse } from '@/types/apiTypes';

/**
 * Fetches the list of available trivia packs from the backend.
 * @returns The response containing the list of packs.
 * @throws If the API request fails.
 */
export const fetchPacks = async (): Promise<ApiPackListResponse> => {
  const url = `${API_BASE_URL}/packs/`; // <<< ADDED SLASH
  console.log("Attempting to fetch packs from:", url);

  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
    });

    console.log("Fetch Packs API Response Status:", response.status);

    let responseData: any;
    try {
        responseData = await response.json();
        // console.log("Fetch Packs API Response Data:", responseData); // Log data if needed
    } catch (jsonError) {
        console.error("Failed to parse JSON response from fetchPacks:", jsonError);
        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}: Failed to fetch packs. Invalid response format.`);
        }
        throw new Error(`Failed to parse successful fetchPacks response JSON: ${jsonError}`);
    }


    if (!response.ok) {
      const errorDetail = responseData?.detail || response.statusText || `HTTP error ${response.status}`;
      console.error("API Error Detail (fetchPacks):", errorDetail);
      throw new Error(`Failed to fetch packs: ${errorDetail}`);
    }

    // Basic validation
    if (!responseData || typeof responseData.total !== 'number' || !Array.isArray(responseData.packs)) {
        console.error("Invalid packs list structure received:", responseData);
        throw new Error("Received invalid pack list data from server.");
    }

    console.log(`Successfully fetched ${responseData.packs.length} packs.`);
    return responseData as ApiPackListResponse;

  } catch (error) {
    console.error("Error fetching packs:", error);
    // Re-throw the error to be caught by the calling component
    throw error;
  }
};

// --- END OF FILE ---