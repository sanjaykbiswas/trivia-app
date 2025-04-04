// src/hooks/useGameTimer.ts
import { useState, useEffect, useRef } from 'react';

/**
 * Custom hook to manage a countdown timer, now resettable via a key dependency.
 * @param timerId A unique identifier for the current timer session (e.g., question ID). Changes trigger reset.
 * @param initialTime The total time for the countdown in seconds.
 * @param isPaused Whether the timer should be paused.
 * @param onTimeout Callback function to execute when the timer reaches zero.
 * @returns The current time remaining in seconds.
 */
export const useGameTimer = (
  timerId: string | number, // <-- NEW: Add a unique ID for the timer instance (like question.id)
  initialTime: number,
  isPaused: boolean,
  onTimeout: () => void
): number => {
  const [timeRemaining, setTimeRemaining] = useState<number>(initialTime);
  const timeoutCallbackRef = useRef(onTimeout); // Use ref for stable callback

  // Update the ref if the onTimeout callback changes
  useEffect(() => {
    timeoutCallbackRef.current = onTimeout;
  }, [onTimeout]);

  // Effect to reset timer when timerId changes (new question) OR initialTime changes
  useEffect(() => {
    console.log(`useGameTimer Reset Effect: Triggered by timerId change to [${timerId}]. Setting time to ${initialTime}`);
    setTimeRemaining(initialTime);
    // This effect now runs whenever the `timerId` (e.g., question.id) changes,
    // forcing the state to reset to the `initialTime` for the new question.
  }, [timerId, initialTime]); // <-- ADD timerId as a dependency

  // Effect to handle the countdown logic
  useEffect(() => {
    if (isPaused) {
      if (timeRemaining <= 0) setTimeRemaining(0);
      return; // Do nothing if paused
    }

    if (timeRemaining <= 0) {
      setTimeRemaining(0);
      // Use a microtask or short timeout to ensure state update happens before callback
      queueMicrotask(() => {
        if (timeoutCallbackRef.current) { // Check ref existence
             console.log(`useGameTimer Countdown Effect: Time reached 0 for timerId [${timerId}]. Calling onTimeout.`);
             timeoutCallbackRef.current();
        } else {
             console.warn(`useGameTimer Countdown Effect: onTimeout ref is null when trying to call for timerId [${timerId}]`);
        }
      });
      return; // Stop the effect
    }

    // Set up the interval timer
    const intervalId = setInterval(() => {
      setTimeRemaining(prevTime => {
        const newTime = prevTime - 0.1;
        if (newTime <= 0) {
          clearInterval(intervalId); // Stop interval immediately
          return 0; // Set to exactly 0
        }
        return newTime;
      });
    }, 100); // Update every 100ms

    // Cleanup function
    return () => {
      clearInterval(intervalId);
    };

    // Depend on `isPaused` and `timeRemaining` for countdown logic.
    // Crucially, DO NOT depend on `timerId` here, as that would restart the interval unnecessarily.
  }, [timeRemaining, isPaused]);
    // --- Removed timerId from this effect's dependency array ---

  // Return the current time, ensuring it's not negative
  return Math.max(0, timeRemaining);
};