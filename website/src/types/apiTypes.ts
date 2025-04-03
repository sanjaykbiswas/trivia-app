// website/src/types/apiTypes.ts
// --- START OF FILE ---

// --- User API Types ---
// Matches backend UserCreateRequest (body)
export interface ApiUserCreateRequest {
  displayname?: string | null; // Optional display name
  email?: string | null; // Optional email
  is_temporary: boolean;
  auth_provider?: string | null; // Optional
  auth_id?: string | null; // Optional
}

// Matches backend UserResponse
export interface ApiUserResponse {
  id: string; // The important part we need
  displayname: string | null;
  email: string | null;
  is_temporary: boolean;
  created_at: string; // ISO date string
  // auth_provider and auth_id might also be present but optional
}
// --- END User API Types ---


// --- Game API Types ---
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

// Matches backend GameSessionJoinRequest (body)
// <<< --- THIS IS THE MISSING INTERFACE --- >>>
export interface ApiGameJoinRequest {
    game_code: string;
    display_name: string;
}
// <<< --- END MISSING INTERFACE --- >>>

// --- Pack API Types ---
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
// --- END Pack API Types ---


// Add other API request/response types as needed...

// --- END OF FILE ---