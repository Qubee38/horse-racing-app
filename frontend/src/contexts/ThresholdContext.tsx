// frontend/src/contexts/ThresholdContext.tsx (新規作成)

import React, { createContext, useContext, useState, useEffect } from 'react';

interface ThresholdContextType {
  winThreshold: number;
  placeThreshold: number;
  setWinThreshold: (value: number) => void;
  setPlaceThreshold: (value: number) => void;
}

const ThresholdContext = createContext<ThresholdContextType | undefined>(undefined);

const STORAGE_KEY = 'probability_thresholds';

export const ThresholdProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [winThreshold, setWinThresholdState] = useState<number>(80);
  const [placeThreshold, setPlaceThresholdState] = useState<number>(85);

  // 初回読み込み
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        setWinThresholdState(parsed.win || 80);
        setPlaceThresholdState(parsed.place || 85);
      } catch (e) {
        console.error('Failed to load thresholds:', e);
      }
    }
  }, []);

  const setWinThreshold = (value: number) => {
    setWinThresholdState(value);
    const current = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ ...current, win: value }));
  };

  const setPlaceThreshold = (value: number) => {
    setPlaceThresholdState(value);
    const current = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ ...current, place: value }));
  };

  return (
    <ThresholdContext.Provider value={{ winThreshold, placeThreshold, setWinThreshold, setPlaceThreshold }}>
      {children}
    </ThresholdContext.Provider>
  );
};

export const useThreshold = () => {
  const context = useContext(ThresholdContext);
  if (!context) {
    throw new Error('useThreshold must be used within ThresholdProvider');
  }
  return context;
};