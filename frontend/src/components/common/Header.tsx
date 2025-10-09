import React from 'react';
import { Trophy, User, ArrowLeft } from 'lucide-react';

// Headerコンポーネントのプロパティ型定義
interface HeaderProps {
  title: string;               // 画面タイトル
  showBackButton?: boolean;    // 戻るボタンの表示/非表示
  onBack?: () => void;         // 戻るボタンがクリックされた時の処理
  onHomeClick?: () => void;    // ホームクリック時の処理（追加）
  children?: React.ReactNode;  // タイトル右側に配置する追加要素（予測実行ボタンなど）
}

/**
 * 全画面共通のヘッダーコンポーネント（修正版）
 * - タイトルクリックでホーム遷移機能追加
 * - React Router不要の実装
 */
const Header: React.FC<HeaderProps> = ({ 
  title, 
  showBackButton = false, 
  onBack,
  onHomeClick,
  children 
}) => {
  // === 修正1: タイトルクリックでホーム遷移 ===
  const handleTitleClick = () => {
    if (onHomeClick) {
      onHomeClick();
    } else {
      // フォールバック: ページリロード
      window.location.href = '/';
    }
  };

  return (
    <div className="relative">
      {/* メインヘッダー: アプリ名とユーザーボタン */}
      <div className="bg-gradient-to-r from-primary-600 to-primary-700 text-white shadow-lg">
        <div className="container-responsive py-4">
          <div className="flex justify-between items-center">
            {/* アプリ名とアイコン - クリック可能に変更 */}
            <button
              onClick={handleTitleClick}
              className="flex items-center gap-3 hover:opacity-90 transition-opacity duration-200 cursor-pointer"
            >
              <div className="bg-white bg-opacity-20 p-2 rounded-lg">
                <Trophy className="w-6 h-6 text-white" />
              </div>
              <div className="text-left">
                <h1 className="text-xl font-bold">競馬予測アプリ</h1>
                <p className="text-sm text-primary-100 hidden sm:block">
                  AI-powered Horse Racing Predictions
                </p>
              </div>
            </button>
            
            {/* ユーザーボタン（将来のユーザー機能用） */}
            <button className="bg-white bg-opacity-20 hover:bg-opacity-30 p-2 rounded-lg transition-all duration-200 group">
              <User className="w-6 h-6 text-white group-hover:scale-110 transition-transform duration-200" />
            </button>
          </div>
        </div>
      </div>
      
      {/* サブヘッダー: 画面タイトルと戻るボタン */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="container-responsive py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              {/* 戻るボタン（条件付きで表示） */}
              {showBackButton && (
                <button 
                  onClick={onBack}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors duration-200 group"
                  aria-label="戻る"
                >
                  <ArrowLeft className="w-5 h-5 text-gray-600 group-hover:text-primary-600 group-hover:translate-x-0.5 transition-all duration-200" />
                </button>
              )}
              
              {/* 画面タイトル */}
              <div>
                <h2 className="text-lg font-bold text-gray-800 animate-fade-in">
                  {title}
                </h2>
                {showBackButton && (
                  <div className="flex items-center gap-1 mt-1">
                    <div className="w-2 h-2 bg-primary-500 rounded-full"></div>
                    <div className="w-1 h-1 bg-primary-300 rounded-full"></div>
                    <div className="w-1 h-1 bg-primary-200 rounded-full"></div>
                  </div>
                )}
              </div>
            </div>
            
            {/* 右側のアクションエリア（予測実行ボタンなど） */}
            <div className="animate-fade-in">
              {children}
            </div>
          </div>
        </div>
      </div>
      
      {/* 装飾的なボトムライン */}
      <div className="h-1 bg-gradient-to-r from-primary-500 via-success-500 to-warning-500"></div>
    </div>
  );
};

export default Header;