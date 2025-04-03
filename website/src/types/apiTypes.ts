// website/src/types/apiTypes.ts
// --- START OF FILE ---

// Matches backend GameSessionCreateRequest (body)
export interface GameCreationPayload {
  pack_id: string;
  max_participants: number;
  question_count: number;
  time_limit_seconds: number;
}

// Matches relevant parts of backend GameSessionResponse
export interface ApiGameSessionResponse {
  id: string;
  code: string;
  status: string; // "pending", "active", etc.
  pack_id: string;
  max_participants: number;
  question_count: number;
  time_limit_seconds: number;
  current_question_index: number;
  participant_count: number;
  is_host: boolean;
  created_at: string; // ISO date string
}

// --- NEW: Types for Fetching Packs ---
// Matches backend PackResponse schema
export interface ApiPackResponse {
    id: string;
    name: string;
    description: string | null;
    price: number;
    pack_group_id: string[] | null;
    creator_type: 'system' | 'user'; // Matches CreatorType enum values
    correct_answer_rate: number | null;
    created_at: string; // ISO date string
    // Add seed_questions and custom_difficulty_description if needed later
}

// Matches backend PackListResponse schema
export interface ApiPackListResponse {
    total: number;
    packs: ApiPackResponse[];
}

// --- END NEW ---

// Add other API request/response types as needed...

// --- END OF FILE ---