// website/src/types/apiTypes.ts
// --- START OF FULL MODIFIED FILE ---

// --- User API Types ---
// Matches backend UserCreateRequest (body)
export interface ApiUserCreateRequest {
  displayname?: string | null;
  email?: string | null;
  is_temporary: boolean;
  auth_provider?: string | null;
  auth_id?: string | null;
}

// Matches backend UserResponse
export interface ApiUserResponse {
  id: string;
  displayname: string | null;
  email: string | null;
  is_temporary: boolean;
  created_at: string; // ISO date string
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
export interface ApiGameJoinRequest {
    game_code: string;
    display_name: string;
}

// Matches backend GameQuestionInfo
export interface ApiGameQuestionInfo {
    index: number;
    question_text: string;
    options: string[];
    time_limit: number;
}

// Matches backend GameStartResponse
export interface ApiGameStartResponse {
    status: string; // e.g., "active"
    current_question: ApiGameQuestionInfo;
}

// Matches the participant structure returned by the GET /participants endpoint
export interface ApiParticipant {
    id: string; // This is the participant record ID
    user_id: string; // The actual User ID
    display_name: string;
    score: number;
    is_host: boolean;
}

// Matches the structure of the GET /participants response
export interface ApiParticipantListResponse {
    total: number;
    participants: ApiParticipant[];
}

// --- NEW TYPES FOR /play-questions ---
// Matches backend GamePlayQuestionResponse
export interface ApiGamePlayQuestion {
    index: number;
    question_id: string;
    question_text: string;
    options: string[]; // Shuffled options from backend
    // --- ADDED FIELD ---
    correct_answer_id: string; // ID of the correct answer option (e.g., "q1-option2")
    // --- END ADDED FIELD ---
    time_limit: number; // Time limit per question
}

// Matches backend GamePlayQuestionListResponse
export interface ApiGamePlayQuestionListResponse {
    game_id: string;
    questions: ApiGamePlayQuestion[];
    total_questions: number;
}
// --- END NEW TYPES ---

// --- Pack API Types ---
// Matches backend PackResponse schema
export interface ApiPackResponse {
    id: string;
    name: string;
    description: string | null;
    price: number;
    pack_group_id: string[] | null;
    creator_type: 'system' | 'user';
    correct_answer_rate: number | null;
    created_at: string; // ISO date string
}

// Matches backend PackListResponse schema
export interface ApiPackListResponse {
    total: number;
    packs: ApiPackResponse[];
}
// --- END Pack API Types ---

// --- END OF FILE ---