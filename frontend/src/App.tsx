// frontend/src/App.tsx (Phase1修正版 - 既存コード準拠)

import React, { useState } from 'react';
import HomePage from './pages/HomePage';
import RaceDetailPage from './pages/RaceDetailPage';
import AdminPage from './pages/AdminPage';
import StatisticsPage from './pages/StatisticsPage';
import { ThresholdProvider } from './contexts/ThresholdContext';
import { Race, Horse } from './types/api';
import './index.css';

type ScreenType = 'home' | 'race-detail' | 'horse-detail' | 'admin' | 'statistics';

function App() {
  const [currentScreen, setCurrentScreen] = useState<ScreenType>('home');
  const [selectedRace, setSelectedRace] = useState<Race | null>(null);
  const [selectedHorse, setSelectedHorse] = useState<Horse | null>(null);
  const [allRaces, setAllRaces] = useState<Race[]>([]); // 追加: レース一覧保持

  // 修正: allRacesを受け取る
  const handleRaceSelect = (race: Race, racesForDate?: Race[]) => {
    console.log('Race selected:', race);
    setSelectedRace(race);
    setSelectedHorse(null);
    if (racesForDate) {
      setAllRaces(racesForDate);
    }
    setCurrentScreen('race-detail');
  };

  const handleHorseSelect = (horse: Horse) => {
    console.log('Horse selected:', horse);
    setSelectedHorse(horse);
    setCurrentScreen('horse-detail');
  };

  const handleBackToHome = () => {
    setCurrentScreen('home');
    setSelectedRace(null);
    setSelectedHorse(null);
    setAllRaces([]);
  };

  const handleBackToRace = () => {
    setCurrentScreen('race-detail');
    setSelectedHorse(null);
  };

  const handleGoToAdmin = () => {
    setCurrentScreen('admin');
  };

  const handleGoToStatistics = () => {
    setCurrentScreen('statistics');
  };

  const renderCurrentScreen = () => {
    switch (currentScreen) {
      case 'home':
        return (
          <HomePage 
            onRaceSelect={handleRaceSelect}
            onGoToAdmin={handleGoToAdmin}
            onGoToStatistics={handleGoToStatistics}
          />
        );
      
      case 'race-detail':
        if (!selectedRace) {
          console.error('Race not selected but trying to show race detail');
          setCurrentScreen('home');
          return (
            <HomePage 
              onRaceSelect={handleRaceSelect}
              onGoToAdmin={handleGoToAdmin}
              onGoToStatistics={handleGoToStatistics}
            />
          );
        }
        
        return (
          <RaceDetailPage
            race={selectedRace}
            onBack={handleBackToHome}
            onHorseSelect={handleHorseSelect}
            allRaces={allRaces}
            onRaceSelect={handleRaceSelect}
          />
        );
      
      case 'admin':
        return <AdminPage onBack={handleBackToHome} />;
      
      case 'statistics':
        return <StatisticsPage />;
      
      case 'horse-detail':
        if (!selectedHorse || !selectedRace) {
          console.error('Horse or Race not selected but trying to show horse detail');
          setCurrentScreen('race-detail');
          return selectedRace ? (
            <RaceDetailPage
              race={selectedRace}
              onBack={handleBackToHome}
              onHorseSelect={handleHorseSelect}
              allRaces={allRaces}
              onRaceSelect={handleRaceSelect}
            />
          ) : (
            <HomePage 
              onRaceSelect={handleRaceSelect}
              onGoToAdmin={handleGoToAdmin}
              onGoToStatistics={handleGoToStatistics}
            />
          );
        }
        
        return (
          <div className="min-h-screen bg-gray-50 flex items-center justify-center">
            <div className="bg-white rounded-lg shadow-md p-8 max-w-md w-full mx-4">
              <div className="text-center">
                <h2 className="text-2xl font-bold mb-4 text-gray-800">
                  馬詳細画面
                </h2>
                
                <div className="mb-6 space-y-2">
                  <p className="text-gray-600">
                    <span className="font-semibold">選択された馬:</span>
                  </p>
                  <p className="text-lg font-bold text-blue-600">
                    {selectedHorse.name}
                  </p>
                  <p className="text-sm text-gray-500">
                    騎手: {selectedHorse.jockey}
                  </p>
                  <p className="text-sm text-gray-500">
                    {selectedHorse.frame_number}枠 {selectedHorse.horse_number}番
                  </p>
                </div>
                
                <div className="space-y-3">
                  <button
                    onClick={handleBackToRace}
                    className="w-full bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors"
                  >
                    レース詳細に戻る
                  </button>
                  <button
                    onClick={handleBackToHome}
                    className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    ホームに戻る
                  </button>
                </div>
              </div>
            </div>
          </div>
        );
      
      default:
        console.warn(`Unknown screen: ${currentScreen}`);
        return (
          <HomePage 
            onRaceSelect={handleRaceSelect}
            onGoToAdmin={handleGoToAdmin}
            onGoToStatistics={handleGoToStatistics}
          />
        );
    }
  };

  return (
    <ThresholdProvider>
      <div className="App">
        {renderCurrentScreen()}
      </div>
    </ThresholdProvider>
  );
}

export default App;