import { useState, useCallback } from 'react';

export function useRoomCode() {
  const [roomCode, setRoomCode] = useState('');
  
  const handleRoomCodeChange = useCallback((text: string) => {
    // Only allow digits
    const digitsOnly = text.replace(/[^0-9]/g, '');
    setRoomCode(digitsOnly);
  }, []);
  
  const resetRoomCode = useCallback(() => {
    setRoomCode('');
  }, []);
  
  return {
    roomCode,
    setRoomCode: handleRoomCodeChange,
    isValidRoomCode: roomCode.length === 5,
    resetRoomCode
  };
}