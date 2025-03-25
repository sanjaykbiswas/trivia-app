import { useState, useCallback } from 'react';

export function useModal(initialState = false) {
  const [isVisible, setIsVisible] = useState(initialState);
  
  const showModal = useCallback(() => {
    setIsVisible(true);
  }, []);
  
  const hideModal = useCallback(() => {
    setIsVisible(false);
  }, []);
  
  const toggleModal = useCallback(() => {
    setIsVisible(prev => !prev);
  }, []);
  
  return {
    isVisible,
    showModal,
    hideModal,
    toggleModal
  };
}