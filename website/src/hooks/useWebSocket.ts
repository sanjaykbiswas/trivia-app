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

  // --- connect Function (Stable Reference - Dependencies refined later) ---
  const connect = useCallback(() => {
    // ... (Keep inner logic of connect the same) ...
    if (!gameId || !userId) { console.log(`[WS Connect Skipped] Missing gameId(${gameId}) or userId(${userId})`); return; }
    if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) { console.log(`[WS Connect Skipped - ${gameId}/${userId}] WebSocket already OPEN or CONNECTING (readyState: ${wsRef.current.readyState})`); return; }
    if (attemptingConnectionRef.current) { console.log(`[WS Connect Skipped - ${gameId}/${userId}] Already attempting connection.`); return; }

    const wsUrl = `${WS_BASE_URL}/ws/${gameId}/${userId}`;
    console.log(`[WS Attempting Connect - ${gameId}/${userId}] URL: ${wsUrl}`);
    manualDisconnectRef.current = false;
    attemptingConnectionRef.current = true;
    setStatus('connecting');

    try {
        const newWs = new WebSocket(wsUrl);
        wsRef.current = newWs;

        newWs.onopen = () => {
            if (wsRef.current === newWs) {
                console.log(`[WS Connected - ${gameId}/${userId}] Connection opened.`);
                setStatus('connected');
                retryCountRef.current = 0;
                if (connectTimeoutRef.current) clearTimeout(connectTimeoutRef.current);
                attemptingConnectionRef.current = false;
                if (onOpenRef.current) onOpenRef.current();
            } else {
                 console.warn(`[WS Stale Open Event - ${gameId}/${userId}] Ignoring open event for a previous socket instance.`);
                 newWs.close(1001, "Stale connection attempt");
            }
        };

        newWs.onmessage = (event) => {
            if (wsRef.current === newWs) {
                try { const message: IncomingWsMessage = JSON.parse(event.data); if (onMessageRef.current) onMessageRef.current(message); }
                catch (error) { console.error(`[WS Message Error - ${gameId}/${userId}] Failed to parse:`, error, 'Data:', event.data); }
            }
        };

        newWs.onerror = (event) => {
             if (wsRef.current === newWs) {
                 console.error(`[WS Error - ${gameId}/${userId}]`, event);
                 setStatus('error'); // Set error state on actual error event
                 if (onErrorRef.current) onErrorRef.current(event as Event);
                 // Let onclose handle retry logic etc.
             }
        };

        newWs.onclose = (event) => {
             if (wsRef.current === newWs || wsRef.current === null) {
                 console.log(`[WS Closed Event - ${gameId}/${userId}] Code: ${event.code}, Reason: ${event.reason}`);
                 // Don't set status directly here, let handleClose do it
                 // setStatus('disconnected'); // REMOVE THIS
                 // attemptingConnectionRef.current = false; // Let handleClose reset this
                 // wsRef.current = null; // Let handleClose reset this
                 if (onCloseRef.current) onCloseRef.current(event); // Call onClose callback first

                 // --- Retry Logic Moved Here ---
                 const shouldRetry = !manualDisconnectRef.current && event.code !== 1000;
                 console.log(`[WS onClose - ${gameId}/${userId}] ShouldRetry: ${shouldRetry} (Manual: ${manualDisconnectRef.current}, Code: ${event.code})`);
                 if (shouldRetry && (maxRetries === -1 || retryCountRef.current < maxRetries)) {
                     retryCountRef.current++;
                     const retryMsg = `Attempting reconnect ${retryCountRef.current}/${maxRetries === -1 ? 'infinite' : maxRetries}...`;
                     console.log(`[WS Retry - ${gameId}/${userId}] ${retryMsg}`);
                     toast.info("Connection Lost", { description: retryMsg });
                     if (connectTimeoutRef.current) clearTimeout(connectTimeoutRef.current);
                     connectTimeoutRef.current = setTimeout(() => {
                         // Re-trigger connection attempt via the main effect by ensuring status is disconnected
                         setStatus('disconnected'); // Ensure state triggers effect
                     }, retryInterval);
                 } else {
                    // No retry needed or max retries reached, ensure final state is disconnected
                    setStatus('disconnected');
                    wsRef.current = null; // Clear ref here on final close
                    attemptingConnectionRef.current = false;
                    if (shouldRetry) {
                        console.log(`[WS Retry - ${gameId}/${userId}] Max retries reached or retries disabled.`);
                        toast.error("Connection Lost", { description: "Could not reconnect to the game server." });
                    } else {
                        console.log(`[WS Retry - ${gameId}/${userId}] No retry needed (Manual disconnect or code 1000).`);
                    }
                 }
             } else {
                  console.warn(`[WS Stale Close Event - ${gameId}/${userId}] Ignoring close event for a previous socket instance.`);
             }
        };

    } catch (error) {
        console.error(`[WS Creation Error - ${gameId}/${userId}]`, error);
        setStatus('error');
        attemptingConnectionRef.current = false;
        wsRef.current = null;
        if (onErrorRef.current) onErrorRef.current(new Event("WebSocket Creation Failed"));
        // Trigger disconnect status to potentially allow retry via main effect
        setStatus('disconnected');
    }
  // Only depend on things that identify *which* connection to make
  }, [gameId, userId, retryInterval, maxRetries]);


  // --- disconnect Function (Stable Reference - REMOVED status dependency) ---
  const disconnect = useCallback(() => {
    console.log(`[WS Manual Disconnect - ${gameId}/${userId}] Initiated.`);
    manualDisconnectRef.current = true;

    if (connectTimeoutRef.current) {
      clearTimeout(connectTimeoutRef.current);
      connectTimeoutRef.current = null;
      console.log(`[WS Manual Disconnect - ${gameId}/${userId}] Cleared pending retry timeout.`);
    }

    const currentWs = wsRef.current;
    if (currentWs) {
        console.log(`[WS Manual Disconnect - ${gameId}/${userId}] Closing socket (readyState: ${currentWs.readyState}).`);
        if (currentWs.readyState === WebSocket.OPEN || currentWs.readyState === WebSocket.CONNECTING) {
            // Setting the onclose to null *before* calling close might prevent the retry logic
            // in our custom onclose from firing for a manual disconnect.
            currentWs.onclose = null; // Prevent custom onclose handler
            currentWs.onerror = null; // Prevent error handler
            currentWs.close(1000, 'User initiated disconnect');
        }
        wsRef.current = null;
    } else {
         console.log(`[WS Manual Disconnect - ${gameId}/${userId}] No active socket to close.`);
    }

    // Immediately set status to disconnected for manual calls
    setStatus('disconnected');
    attemptingConnectionRef.current = false;

  // Only needs IDs to know *which* logical connection it pertains to, if any logic inside used them.
  // Since it primarily operates on refs, it can often have fewer deps.
  }, [gameId, userId]);


  // --- Primary Connection Effect ---
  useEffect(() => {
      console.log(`[WS useEffect Check - ${gameId}/${userId}] Current Status: ${status}, Attempting: ${attemptingConnectionRef.current}`);
      if (gameId && userId) {
          // Attempt connection only if truly disconnected and not already trying
          if (status === 'disconnected' && !attemptingConnectionRef.current) {
              console.log(`[WS useEffect Trigger Connect - ${gameId}/${userId}]`);
              retryCountRef.current = 0; // Reset retries for a new connection sequence
              manualDisconnectRef.current = false; // Allow retries for this new connection attempt
              connect(); // Call the stable connect function
          } else {
              console.log(`[WS useEffect Skip Connect - ${gameId}/${userId}] Conditions not met (status: ${status}, attempting: ${attemptingConnectionRef.current})`);
          }
      } else {
          // IDs are missing or invalid, ensure disconnection if needed
          if (status === 'connected' || status === 'connecting' || attemptingConnectionRef.current) {
              console.log(`[WS useEffect Trigger Disconnect - ${gameId}/${userId}] IDs invalid (${gameId}, ${userId}) or no longer valid, status: ${status}.`);
              disconnect(); // Call the stable disconnect function
          } else {
               console.log(`[WS useEffect Skip Disconnect - ${gameId}/${userId}] IDs invalid, status: ${status}.`);
          }
      }

      // --- Cleanup Logic ---
      return () => {
          // No changes needed here - the stable disconnect handles cleanup correctly
          // This cleanup runs when the component unmounts OR gameId/userId changes
          console.log(`[WS Cleanup - ${gameId}/${userId}] Unmounting or deps changed.`);
          disconnect(); // Call stable disconnect on cleanup

          // Also clear any pending retry timer explicitly on unmount/dependency change
           if (connectTimeoutRef.current) {
              console.log(`[WS Cleanup - ${gameId}/${userId}] Clearing retry timer on cleanup.`);
              clearTimeout(connectTimeoutRef.current);
              connectTimeoutRef.current = null;
           }
      };
  // Rerun only if gameId or userId changes. connect/disconnect are now stable.
  }, [gameId, userId, connect, disconnect]); // Keep connect/disconnect here


  return { status };
};