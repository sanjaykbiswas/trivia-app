// website/src/hooks/useWebSocket.ts
import { useState, useEffect, useRef, useCallback } from 'react';
import { toast } from 'sonner';
import { IncomingWsMessage } from '@/types/websocketTypes'; // Import message types
import { API_BASE_URL } from '@/config';

// Define WebSocket connection states
type WebSocketStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

interface UseWebSocketOptions {
  gameId: string | null;
  userId: string | null;
  onMessage: (message: IncomingWsMessage) => void; // Callback to handle received messages
  onError?: (event: Event) => void;
  onOpen?: () => void;
  onClose?: (event: CloseEvent) => void;
  retryInterval?: number; // Time in ms between reconnection attempts
  maxRetries?: number; // Max number of reconnection attempts (-1 for infinite)
}

const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || API_BASE_URL.replace(/^http/, 'ws');
console.log("WebSocket Base URL:", WS_BASE_URL);


/**
 * Custom hook to manage a WebSocket connection for the game.
 * Handles connection, disconnection, message sending/receiving, and basic reconnection.
 */
export const useWebSocket = ({
  gameId,
  userId,
  onMessage,
  onError,
  onOpen,
  onClose,
  retryInterval = 5000, // Default 5 seconds
  maxRetries = 5,       // Default 5 retries
}: UseWebSocketOptions) => {
  const [status, setStatus] = useState<WebSocketStatus>('disconnected');
  const wsRef = useRef<WebSocket | null>(null);
  const retryCountRef = useRef<number>(0);
  const connectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const attemptingConnectionRef = useRef<boolean>(false); // Flag to prevent concurrent connection attempts

  // Stable callback refs
  const onMessageRef = useRef(onMessage);
  const onErrorRef = useRef(onError);
  const onOpenRef = useRef(onOpen);
  const onCloseRef = useRef(onClose);

  useEffect(() => { onMessageRef.current = onMessage; }, [onMessage]);
  useEffect(() => { onErrorRef.current = onError; }, [onError]);
  useEffect(() => { onOpenRef.current = onOpen; }, [onOpen]);
  useEffect(() => { onCloseRef.current = onClose; }, [onClose]);

  const connect = useCallback(() => {
    // Prevent connection if missing required IDs or already connecting/connected
    if (!gameId || !userId || attemptingConnectionRef.current || status === 'connected' || status === 'connecting') {
      if (!gameId || !userId) console.log("WebSocket connect skipped: Missing gameId or userId");
      else console.log(`WebSocket connect skipped: Status is ${status} or already attempting.`);
      return;
    }

    // Construct WebSocket URL
    const wsUrl = `${WS_BASE_URL}/ws/${gameId}/${userId}`;
    console.log(`Attempting WebSocket connection to: ${wsUrl}`);

    attemptingConnectionRef.current = true; // Set flag
    setStatus('connecting');
    retryCountRef.current = 0; // Reset retry count on new manual connect attempt

    try {
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('WebSocket connection opened');
        setStatus('connected');
        retryCountRef.current = 0; // Reset retries on successful connection
        if (connectTimeoutRef.current) clearTimeout(connectTimeoutRef.current);
        attemptingConnectionRef.current = false; // Clear flag
        if (onOpenRef.current) onOpenRef.current();
      };

      wsRef.current.onmessage = (event) => {
        try {
          const message: IncomingWsMessage = JSON.parse(event.data);
          // console.log('WebSocket message received:', message); // Debug log
          if (onMessageRef.current) onMessageRef.current(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error, 'Data:', event.data);
        }
      };

      wsRef.current.onerror = (event) => {
        console.error('WebSocket error:', event);
        setStatus('error');
        attemptingConnectionRef.current = false; // Clear flag on error too
        if (onErrorRef.current) onErrorRef.current(event);
        // Optionally trigger reconnection logic here as well
        handleClose(new CloseEvent('errorclose')); // Treat error as a close event for potential retry
      };

      wsRef.current.onclose = (event) => {
        console.log('WebSocket connection closed:', event.code, event.reason);
        handleClose(event);
      };

    } catch (error) {
        console.error("Error creating WebSocket:", error);
        setStatus('error');
        attemptingConnectionRef.current = false; // Clear flag
        // Handle creation error, maybe retry?
    }

  }, [gameId, userId, status]); // Depends on IDs and status to prevent multiple connects

  const handleClose = useCallback((event: CloseEvent) => {
      setStatus('disconnected');
      attemptingConnectionRef.current = false; // Clear flag
      wsRef.current = null; // Clear the ref
      if (onCloseRef.current) onCloseRef.current(event);

      // Reconnection logic
      if ((maxRetries === -1 || retryCountRef.current < maxRetries)) {
         retryCountRef.current++;
         console.log(`WebSocket closed. Attempting reconnect ${retryCountRef.current}/${maxRetries === -1 ? 'infinite' : maxRetries}...`);
         toast.info("Connection Lost", { description: `Attempting to reconnect (${retryCountRef.current})...`});
         if (connectTimeoutRef.current) clearTimeout(connectTimeoutRef.current); // Clear previous timeout
         connectTimeoutRef.current = setTimeout(connect, retryInterval);
      } else {
         console.log("WebSocket closed. Max retries reached or retries disabled.");
         toast.error("Connection Lost", { description: "Could not reconnect to the game server."});
      }
  }, [maxRetries, retryInterval, connect]); // Added `connect` to dependencies

  const disconnect = useCallback(() => {
    if (connectTimeoutRef.current) {
      clearTimeout(connectTimeoutRef.current); // Cancel any pending reconnection attempts
      connectTimeoutRef.current = null;
    }
    retryCountRef.current = maxRetries; // Prevent further retries after manual disconnect
    if (wsRef.current) {
      console.log('Manually closing WebSocket connection.');
      wsRef.current.close(1000, 'User disconnected'); // Use standard code 1000
      // wsRef.current = null; // Let onclose handle setting ref to null
      // setStatus('disconnected'); // Let onclose handle status update
    }
  }, [maxRetries]);

  // Effect to initiate connection when gameId and userId are available
  useEffect(() => {
    if (gameId && userId) {
      connect();
    } else {
      // If IDs become null/undefined, ensure disconnection
      disconnect();
    }

    // Cleanup on unmount or when IDs change significantly
    return () => {
      console.log("useWebSocket cleanup: Disconnecting...");
      disconnect();
    };
  }, [gameId, userId, connect, disconnect]); // Add connect/disconnect

  // Function to send messages (if needed later)
  // const sendMessage = useCallback((message: any) => {
  //   if (wsRef.current && status === 'connected') {
  //     try {
  //       wsRef.current.send(JSON.stringify(message));
  //     } catch (error) {
  //       console.error("Failed to send WebSocket message:", error);
  //     }
  //   } else {
  //     console.warn("WebSocket not connected. Cannot send message:", message);
  //   }
  // }, [status]);

  return { status }; // Expose status, maybe sendMessage later
};