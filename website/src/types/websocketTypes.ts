// website/src/types/websocketTypes.ts

import { ApiParticipant, ApiGameSessionResponse, ApiGamePlayQuestion } from './apiTypes'; // Assuming these are defined

// --------- Message Types Sent FROM Backend TO Frontend ---------

/** Message indicating a user joined or their info updated (e.g., name change) */
export interface WsParticipantUpdatePayload extends ApiParticipant {}
export interface WsParticipantUpdateMessage {
    type: 'participant_update';
    payload: WsParticipantUpdatePayload;
}

/** Message indicating a user left the game */
export interface WsParticipantLeftPayload {
    user_id: string; // ID of the user who left
    participant_id: string; // ID of the participant record
    display_name: string; // Name of the user who left (for potential notification)
}
export interface WsParticipantLeftMessage {
    type: 'participant_left';
    payload: WsParticipantLeftPayload;
}

/** Message indicating a user's display name changed */
export interface WsUserNameUpdatedPayload {
    user_id: string;
    new_display_name: string;
}
export interface WsUserNameUpdatedMessage {
    type: 'user_name_updated';
    payload: WsUserNameUpdatedPayload;
}

/** Message indicating the game has started (sent by host action) */
export interface WsGameStartedPayload {
    game_id: string;
    status: string; // Should be 'active'
    total_questions: number;
    time_limit: number;
    pack_id: string;
    current_question: ApiGamePlayQuestion | null; // Include the first question
}
export interface WsGameStartedMessage {
    type: 'game_started';
    payload: WsGameStartedPayload;
}

/** Message indicating the next question is ready */
export interface WsNextQuestionPayload extends ApiGamePlayQuestion {} // Re-use the existing API type
export interface WsNextQuestionMessage {
    type: 'next_question';
    payload: WsNextQuestionPayload;
}

/** Message indicating the game is over and includes final results */
export interface WsGameOverPayload {
    // Structure should match the response from GET /games/{game_id}/results
    game_id: string;
    game_code: string;
    status: string; // Should be 'completed' or 'cancelled'
    participants: ApiParticipant[]; // Final scores included here
    questions: any[]; // Include question result summaries if needed
    total_questions: number;
    completed_at: string; // ISO date string
}
export interface WsGameOverMessage {
    type: 'game_over';
    payload: WsGameOverPayload;
}

/** Message indicating the game was cancelled by the host */
export interface WsGameCancelledPayload {
    game_id: string;
}
export interface WsGameCancelledMessage {
    type: 'game_cancelled';
    payload: WsGameCancelledPayload;
}

/** Generic error message from the backend via WebSocket */
export interface WsErrorPayload {
    message: string;
    detail?: string;
}
export interface WsErrorMessage {
    type: 'error';
    payload: WsErrorPayload;
}

// --------- Union Type for ALL Incoming Messages ---------
export type IncomingWsMessage =
    | WsParticipantUpdateMessage
    | WsParticipantLeftMessage
    | WsUserNameUpdatedMessage
    | WsGameStartedMessage
    | WsNextQuestionMessage
    | WsGameOverMessage
    | WsGameCancelledMessage
    | WsErrorMessage;


// --------- Message Types Sent FROM Frontend TO Backend ---------
// (Currently, we are not planning to send messages from client to server,
// but you could define them here if needed, e.g., for submitting answers via WS)

// Example:
// export interface WsSubmitAnswerPayload {
//     question_index: number;
//     answer_id: string;
// }
// export interface WsSubmitAnswerMessage {
//     type: 'submit_answer';
//     payload: WsSubmitAnswerPayload;
// }
// export type OutgoingWsMessage = WsSubmitAnswerMessage;