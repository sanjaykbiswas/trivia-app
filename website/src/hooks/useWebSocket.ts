// website/src/hooks/useWebSocket.ts
import { useState, useEffect, useRef, useCallback } from 'react';
import { toast } from 'sonner';
import { IncomingWsMessage } from '@/types/websocketTypes';
import { API_BASE_URL } from '@/config';

// Define WebSocket connection states
type WebSocketStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

interface UseWebSocketOptions {
  gameId: string | null;
  userId: string | null;
  onMessage: (message: IncomingWsMessage) => void; // Callback to handle received messages
  onError?: (event: Event | CloseEvent) => void; // Allow CloseEvent for error handling context
  onOpen?: () => void; // Callback when connection successfully opens
  onClose?: (event: CloseEvent) => void;
  retryInterval?: number; // Time in ms between reconnection attempts
  maxRetries?: number; // Max number of reconnection attempts (-1 for infinite)
}

const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || API_BASE_URL.replace(/^http/, 'ws');
console.log("WebSocket Base URL:", WS_BASE_URL);


/**
 * Custom hook to manage a WebSocket connection for the game.
 * Handles connection, disconnection, message sending/receiving, and basic reconnection.
 * Refined connection logic and cleanup to prevent premature closure.
 */
export const useWebSocket = ({
  gameId,
  userId,
  onMessage,
  onError,
  onOpen,
  onClose,
  retryInterval = 5000,
  maxRetries = 5,
}: UseWebSocketOptions) => {
  const [status, setStatus] = useState<WebSocketStatus>('disconnected');
  const wsRef = useRef<WebSocket | null>(null);
  const retryCountRef = useRef<number>(0);
  const connectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const attemptingConnectionRef = useRef<boolean>(false);
  // --- NEW: Ref to track if a manual disconnect was requested ---
  const manualDisconnectRef = useRef<boolean>(false);

  // Stable callback refs
  const onMessageRef = useRef(onMessage);
  const onErrorRef = useRef(onError);
  const onOpenRef = useRef(onOpen);
  const onCloseRef = useRef(onClose);

  useEffect(() => { onMessageRef.current = onMessage; }, [onMessage]);
  useEffect(() => { onErrorRef.current = onError; }, [onError]);
  useEffect(() => { onOpenRef.current = onOpen; }, [onOpen]);
  useEffect(() => { onCloseRef.current = onClose; }, [onClose]);

  // --- handleClose Function ---
  // Moved before connect/disconnect as they reference it
  const handleClose = useCallback((event: CloseEvent) => {
      const wasAttempting = attemptingConnectionRef.current;
      const wasConnected = status === 'connected'; // Check status *before* setting disconnected

      // Only process if not already marked as disconnected by our logic
      if (status !== 'disconnected') {
        console.log(`[WS handleClose - ${gameId}/${userId}] Status was ${status}. Setting disconnected. Code: ${event.code}`);
        setStatus('disconnected');
      } else {
         console.log(`[WS handleClose - ${gameId}/${userId}] Already disconnected. Code: ${event.code}`);
      }

      attemptingConnectionRef.current = false; // Always reset flag on close
      wsRef.current = null; // Clear the ref

      if (onCloseRef.current) {
          onCloseRef.current(event);
      }

      // Reconnection logic
      // Avoid retry if manually disconnected or clean close (code 1000)
      const shouldRetry = !manualDisconnectRef.current && event.code !== 1000;
      console.log(`[WS handleClose - ${gameId}/${userId}] ShouldRetry: ${shouldRetry} (Manual: ${manualDisconnectRef.current}, Code: ${event.code})`);

      if (shouldRetry && (maxRetries === -1 || retryCountRef.current < maxRetries)) {
          retryCountRef.current++;
          const retryMsg = `Attempting reconnect ${retryCountRef.current}/${maxRetries === -1 ? 'infinite' : maxRetries}...`;
          console.log(`[WS Retry - ${gameId}/${userId}] ${retryMsg}`);
          toast.info("Connection Lost", { description: retryMsg });
          if (connectTimeoutRef.current) clearTimeout(connectTimeoutRef.current);
          connectTimeoutRef.current = setTimeout(() => {
              // Check if IDs are still valid before retrying connection
              // Note: 'connect' reference might be stale here, directly check props? Or pass connect?
              // Let's assume connect uses the latest props/state via its own closure.
              if (gameId && userId) {
                   // Re-call connect (which is stable via useCallback)
                   // connect will check its own preconditions again
                   connect();
              } else {
                   console.log(`[WS Retry Aborted - ${gameId}/${userId}] IDs became invalid.`);
              }
          }, retryInterval);
      } else if (shouldRetry) {
          console.log(`[WS Retry - ${gameId}/${userId}] Max retries reached or retries disabled.`);
          toast.error("Connection Lost", { description: "Could not reconnect to the game server." });
      } else {
           console.log(`[WS Retry - ${gameId}/${userId}] No retry needed (Manual disconnect or code 1000).`);
      }
  }, [maxRetries, retryInterval, onCloseRef, status, gameId, userId]); // Added status, gameId, userId - connect itself is stable


  // --- connect Function (Stable Reference) ---
  const connect = useCallback(() => {
    if (!gameId || !userId) { console.log(`[WS Connect Skipped] Missing gameId(${gameId}) or userId(${userId})`); return; }
    // Check readyState directly for more accurate current status
    if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
       console.log(`[WS Connect Skipped - ${gameId}/${userId}] WebSocket already OPEN or CONNECTING (readyState: ${wsRef.current.readyState})`); return;
    }
     if (attemptingConnectionRef.current) {
        console.log(`[WS Connect Skipped - ${gameId}/${userId}] Already attempting connection.`); return;
     }

    const wsUrl = `${WS_BASE_URL}/ws/${gameId}/${userId}`;
    console.log(`[WS Attempting Connect - ${gameId}/${userId}] URL: ${wsUrl}`);

    manualDisconnectRef.current = false; // Reset manual flag on new attempt
    attemptingConnectionRef.current = true;
    setStatus('connecting');
    // Reset retry count ONLY on a new *manual* connect intent (handled in useEffect)

    try {
        const newWs = new WebSocket(wsUrl);
        wsRef.current = newWs; // Assign immediately

        newWs.onopen = () => {
             // Double-check if this is still the active socket attempt
            if (wsRef.current === newWs) {
                console.log(`[WS Connected - ${gameId}/${userId}] Connection opened.`);
                setStatus('connected');
                retryCountRef.current = 0;
                if (connectTimeoutRef.current) clearTimeout(connectTimeoutRef.current);
                attemptingConnectionRef.current = false;
                if (onOpenRef.current) onOpenRef.current();
            } else {
                 console.warn(`[WS Stale Open Event - ${gameId}/${userId}] Ignoring open event for a previous socket instance.`);
                 // Close this potentially orphaned connection if it's not the current one
                 newWs.close(1001, "Stale connection attempt");
            }
        };

        newWs.onmessage = (event) => {
            if (wsRef.current === newWs) { // Ensure message is from the active socket
                try { const message: IncomingWsMessage = JSON.parse(event.data); if (onMessageRef.current) onMessageRef.current(message); }
                catch (error) { console.error(`[WS Message Error - ${gameId}/${userId}] Failed to parse:`, error, 'Data:', event.data); }
            }
        };

        newWs.onerror = (event) => {
             if (wsRef.current === newWs) { // Ensure error is from the active socket
                 console.error(`[WS Error - ${gameId}/${userId}]`, event);
                 if (onErrorRef.current) onErrorRef.current(event as Event); // Pass original event
                 // Let onclose handle the state change and retry logic
             }
        };

        newWs.onclose = (event) => {
             // Only handle close if it's the currently managed socket ref
             // Or if the ref is null but we were expecting a close
             if (wsRef.current === newWs || wsRef.current === null) {
                 console.log(`[WS Closed Event - ${gameId}/${userId}] Code: ${event.code}, Reason: ${event.reason}`);
                 handleClose(event);
             } else {
                  console.warn(`[WS Stale Close Event - ${gameId}/${userId}] Ignoring close event for a previous socket instance.`);
             }
        };

    } catch (error) {
        console.error(`[WS Creation Error - ${gameId}/${userId}]`, error);
        setStatus('error'); // Set error status
        attemptingConnectionRef.current = false;
        wsRef.current = null; // Ensure ref is cleared
        if (onErrorRef.current) onErrorRef.current(new Event("WebSocket Creation Failed")); // Pass generic event
        // Trigger close handling for potential retry
        handleClose(new CloseEvent('createerror', { code: 1006, reason: "WebSocket creation failed" }));
    }
  }, [gameId, userId, handleClose]); // handleClose is now stable


  // --- disconnect Function (Stable Reference) ---
  const disconnect = useCallback(() => {
    console.log(`[WS Manual Disconnect - ${gameId}/${userId}] Initiated.`);
    manualDisconnectRef.current = true; // Set flag to prevent retries

    if (connectTimeoutRef.current) {
      clearTimeout(connectTimeoutRef.current);
      connectTimeoutRef.current = null;
      console.log(`[WS Manual Disconnect - ${gameId}/${userId}] Cleared pending retry timeout.`);
    }

    const currentWs = wsRef.current; // Capture current ref
    if (currentWs) {
        console.log(`[WS Manual Disconnect - ${gameId}/${userId}] Closing socket (readyState: ${currentWs.readyState}).`);
        // Check readyState before closing - avoids errors if already closing/closed
        if (currentWs.readyState === WebSocket.OPEN || currentWs.readyState === WebSocket.CONNECTING) {
            currentWs.close(1000, 'User initiated disconnect');
        }
        wsRef.current = null; // Clear ref immediately
    } else {
         console.log(`[WS Manual Disconnect - ${gameId}/${userId}] No active socket to close.`);
    }

    // Ensure status is updated immediately for manual disconnect
    if (status !== 'disconnected') {
        setStatus('disconnected');
    }
    attemptingConnectionRef.current = false; // Reset flag

  }, [status]); // Depends on status


  // --- Primary Connection Effect ---
  useEffect(() => {
      console.log(`[WS useEffect Check - ${gameId}/${userId}] Current Status: ${status}, Attempting: ${attemptingConnectionRef.current}`);
      if (gameId && userId) {
          // Attempt connection only if disconnected and not already trying
          if (status === 'disconnected' && !attemptingConnectionRef.current) {
              console.log(`[WS useEffect Trigger Connect - ${gameId}/${userId}]`);
              retryCountRef.current = 0; // Reset retries when explicitly trying to connect due to ID availability
              manualDisconnectRef.current = false; // Allow retries for this new connection attempt
              connect();
          } else {
              console.log(`[WS useEffect Skip Connect - ${gameId}/${userId}] Conditions not met (status: ${status}, attempting: ${attemptingConnectionRef.current})`);
          }
      } else {
          // IDs are missing or invalid, ensure disconnection
          if (status === 'connected' || status === 'connecting') {
              console.log(`[WS useEffect Trigger Disconnect - ${gameId}/${userId}] IDs invalid (${gameId}, ${userId}), status: ${status}.`);
              disconnect();
          } else {
               console.log(`[WS useEffect Skip Disconnect - ${gameId}/${userId}] IDs invalid, status: ${status}.`);
          }
      }

      // --- Refined Cleanup ---
      return () => {
          const currentStatus = status; // Capture status at the time cleanup is defined
          console.log(`[WS Cleanup - ${gameId}/${userId}] Status: ${currentStatus}. Unmounting or deps changed.`);

          // Only call disconnect if the connection was active or attempting.
          // Avoid calling disconnect if it's already 'disconnected' or in 'error' state from its perspective.
          if (currentStatus === 'connected' || currentStatus === 'connecting') {
               console.log(`[WS Cleanup - ${gameId}/${userId}] Calling disconnect as status was ${currentStatus}.`);
               disconnect();
          } else {
               console.log(`[WS Cleanup - ${gameId}/${userId}] Skipping disconnect call as status was ${currentStatus}.`);
          }

          // Always clear pending retry timers on cleanup
           if (connectTimeoutRef.current) {
              console.log(`[WS Cleanup - ${gameId}/${userId}] Clearing retry timer.`);
              clearTimeout(connectTimeoutRef.current);
              connectTimeoutRef.current = null;
           }
      };
  // connect/disconnect are stable useCallback refs now. Rerun only if gameId/userId changes.
  }, [gameId, userId, connect, disconnect]); // Removed status


  return { status };
};
// --- END OF FILE ---