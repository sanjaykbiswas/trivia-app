import { useState, useCallback } from 'react';

export function useRoomCode() {
  // Store the actual digits (without hyphen)
  const [roomCode, setRoomCode] = useState('');
  
  // Store the displayed value (with hyphen when needed)
  const [displayValue, setDisplayValue] = useState('');
  
  const handleRoomCodeChange = useCallback((text: string) => {
    // Handle special case for pasting hyphenated code
    // Remove all non-digit characters (including hyphens)
    const cleanInput = text.replace(/[^0-9]/g, '');
    
    // Limit to 6 digits
    const digitsOnly = cleanInput.substring(0, 6);
    
    // Store the actual room code digits
    setRoomCode(digitsOnly);
    
    // Format for display with hyphen
    if (digitsOnly.length <= 3) {
      setDisplayValue(digitsOnly);
    } else {
      const firstPart = digitsOnly.substring(0, 3);
      const secondPart = digitsOnly.substring(3);
      setDisplayValue(`${firstPart}-${secondPart}`);
    }
  }, []);
  
  const resetRoomCode = useCallback(() => {
    setRoomCode('');
    setDisplayValue('');
  }, []);
  
  // Format the room code for display with a hyphen (e.g., 123-456)
  const formattedRoomCode = useCallback(() => {
    if (roomCode.length <= 3) {
      return roomCode;
    }
    const firstPart = roomCode.substring(0, 3);
    const secondPart = roomCode.substring(3);
    return `${firstPart}-${secondPart}`;
  }, [roomCode]);
  
  return {
    roomCode,
    displayValue,
    setRoomCode: handleRoomCodeChange,
    formattedRoomCode: formattedRoomCode(),
    isValidRoomCode: roomCode.length === 6,
    resetRoomCode
  };
}