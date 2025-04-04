// website/src/types/apiTypes.ts
// --- START OF FULL MODIFIED FILE ---

// --- User API Types ---
export interface ApiUserCreateRequest {
    displayname?: string | null;
    email?: string | null;
    is_temporary: boolean;
    auth_provider?: string | null;
    auth_id?: string | null;
  }

  export interface ApiUserResponse {
    id: string;
    displayname: string | null;
    email: string | null;
    is_temporary: boolean;
    created_at: string; // ISO date string
  }
  // --- END User API Types ---


  // --- Game API Types ---
  export interface GameCreationPayload {
    pack_id: string;
    max_participants: number;
    question_count: number;
    time_limit_seconds: number;
  }

  export interface ApiGameSessionResponse {
    id: string;
    code: string;
    status: string; // "pending", "active", etc.
    pack_id: string;
    // --- ADDED host_user_id ---
    host_user_id: string; // ID of the actual game host
    // --- END ADDED host_user_id ---
    max_participants: number;
    question_count: number;
    time_limit_seconds: number;
    current_question_index: number;
    participant_count: number;
    is_host: boolean; // Whether the user making the request is the host
    created_at: string; // ISO date string
  }

  export interface ApiGameJoinRequest {
      game_code: string;
      display_name: string;
  }

  export interface ApiGameQuestionInfo {
      index: number;
      question_text: string;
      options: string[];
      time_limit: number;
  }

  export interface ApiGameStartResponse {
      status: string; // e.g., "active"
      current_question: ApiGameQuestionInfo;
  }

  export interface ApiParticipant {
      id: string; // Participant record ID
      user_id: string; // User ID
      display_name: string;
      score: number;
      is_host: boolean;
  }

  export interface ApiParticipantListResponse {
      total: number;
      participants: ApiParticipant[];
  }

  export interface ApiGameSubmitAnswerRequest {
    question_index: number;
    answer: string;
  }

  export interface ApiQuestionResultResponse {
    is_correct: boolean;
    correct_answer: string;
    score: number;
    total_score: number;
  }

  // --- Gameplay Questions ---
  export interface ApiGamePlayQuestion {
      index: number;
      question_id: string;
      question_text: string;
      options: string[];
      correct_answer_id: string;
      time_limit: number;
  }

  export interface ApiGamePlayQuestionListResponse {
      game_id: string;
      questions: ApiGamePlayQuestion[];
      total_questions: number;
  }
  // --- END Gameplay Questions ---

  // --- Pack API Types ---
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

  export interface ApiPackListResponse {
      total: number;
      packs: ApiPackResponse[];
  }
  // --- END Pack API Types ---

  // --- END OF FILE ---