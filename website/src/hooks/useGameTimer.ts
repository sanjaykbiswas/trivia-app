// src/hooks/useGameTimer.ts
import { useState, useEffect, useRef } from 'react';

/**
 * Custom hook to manage a countdown timer.
 * @param initialTime The total time for the countdown in seconds.
 * @param isPaused Whether the timer should be paused.
 * @param onTimeout Callback function to execute when the timer reaches zero.
 * @returns The current time remaining in seconds.
 */
export const useGameTimer = (initialTime: number, isPaused: boolean, onTimeout: () => void): number => {
  const [timeRemaining, setTimeRemaining] = useState<number>(initialTime);
  const timeoutCallbackRef = useRef(onTimeout); // Use ref to avoid effect dependency issues with callbacks

  // Update the ref if the onTimeout callback changes
  useEffect(() => {
    timeoutCallbackRef.current = onTimeout;
  }, [onTimeout]);

  // Effect to reset timer when initialTime changes (new question)
  useEffect(() => {
    setTimeRemaining(initialTime);
  }, [initialTime]);

  // Effect to handle the countdown logic
  useEffect(() => {
    // Ensure time starts correctly even if paused initially
    if (isPaused) {
        // If timer was paused exactly at 0, keep it there
        if (timeRemaining <= 0) setTimeRemaining(0);
        return; // Do nothing if paused
    }

    // Base case: time ran out
    if (timeRemaining <= 0) {
        // Ensure it doesn't go negative visually, then call timeout
        setTimeRemaining(0);
        timeoutCallbackRef.current(); // Call the latest timeout function
      return; // Stop the effect
    }

    // Set up the interval timer
    const timerId = setInterval(() => {
      setTimeRemaining(prevTime => {
        const newTime = prevTime - 0.1;
        if (newTime <= 0) {
          clearInterval(timerId); // Stop interval immediately when reaching zero
          return 0; // Return 0 to trigger the timeout logic in the next render cycle
        }
        return newTime;
      });
    }, 100); // Update every 100ms

    // Cleanup function to clear interval when component unmounts,
    // timer is paused, or timeRemaining hits zero.
    return () => clearInterval(timerId);

  }, [timeRemaining, isPaused]); // Rerun effect if timeRemaining or isPaused changes

  // Return the current time, ensuring it's not negative for display
  return Math.max(0, timeRemaining);
};