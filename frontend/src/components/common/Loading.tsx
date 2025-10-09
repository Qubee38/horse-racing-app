import React from 'react';

// Loadingコンポーネントのプロパティ型定義
interface LoadingProps {
  size?: 'small' | 'medium' | 'large';  // スピナーのサイズ
  message?: string;                      // ローディングメッセージ
  fullScreen?: boolean;                  // 全画面表示するかどうか
  variant?: 'spinner' | 'dots' | 'pulse'; // ローディングアニメーションの種類
  color?: 'primary' | 'secondary' | 'success'; // カラーテーマ
}

/**
 * ローディングスピナーコンポーネント
 * - 複数のアニメーションバリエーション
 * - サイズ・カラー調整可能
 * - 全画面表示モード対応
 */
const Loading: React.FC<LoadingProps> = ({ 
  size = 'medium', 
  message = 'Loading...', 
  fullScreen = false,
  variant = 'spinner',
  color = 'primary'
}) => {
  
  // サイズに応じたCSSクラスを決定
  const getSizeClasses = () => {
    switch (size) {
      case 'small': return { spinner: 'w-4 h-4', text: 'text-sm' };
      case 'large': return { spinner: 'w-12 h-12', text: 'text-lg' };
      default: return { spinner: 'w-8 h-8', text: 'text-base' };
    }
  };

  // カラーテーマに応じたCSSクラスを決定
  const getColorClasses = () => {
    switch (color) {
      case 'secondary': return 'text-gray-600';
      case 'success': return 'text-success-600';
      default: return 'text-primary-600';
    }
  };

  const sizeClasses = getSizeClasses();
  const colorClass = getColorClasses();

  // スピナータイプのローディング
  const SpinnerLoading = () => (
    <div className={`loading-spinner ${sizeClasses.spinner} border-2 border-gray-200 ${colorClass.replace('text-', 'border-t-')}`} />
  );

  // ドットタイプのローディング
  const DotsLoading = () => (
    <div className="flex space-x-1">
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className={`${sizeClasses.spinner.split(' ')[0]} ${sizeClasses.spinner.split(' ')[1]} ${colorClass.replace('text-', 'bg-')} rounded-full animate-bounce`}
          style={{ 
            animationDelay: `${i * 0.1}s`,
            animationDuration: '0.6s'
          }}
        />
      ))}
    </div>
  );

  // パルスタイプのローディング
  const PulseLoading = () => (
    <div className="flex space-x-1">
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className={`${sizeClasses.spinner} ${colorClass.replace('text-', 'bg-')} rounded-full animate-pulse`}
          style={{ 
            animationDelay: `${i * 0.2}s`,
            opacity: 0.7 - i * 0.1
          }}
        />
      ))}
    </div>
  );

  // アニメーションバリエーションを選択
  const renderAnimation = () => {
    switch (variant) {
      case 'dots': return <DotsLoading />;
      case 'pulse': return <PulseLoading />;
      default: return <SpinnerLoading />;
    }
  };

  // ローディングコンテンツ
  const loadingContent = (
    <div className="flex flex-col items-center gap-4 animate-fade-in">
      {/* アニメーション */}
      <div className="relative">
        {renderAnimation()}
        
        {/* 装飾的なリング（大きいサイズの場合のみ） */}
        {size === 'large' && variant === 'spinner' && (
          <div className="absolute inset-0 border border-gray-100 rounded-full animate-ping" 
               style={{ animationDuration: '2s' }} />
        )}
      </div>
      
      {/* メッセージ */}
      <div className="text-center">
        <p className={`${colorClass} ${sizeClasses.text} font-medium animate-pulse`}>
          {message}
        </p>
        
        {/* プログレスドット */}
        <div className="flex justify-center space-x-1 mt-2">
          {[0, 1, 2, 3].map((i) => (
            <div
              key={i}
              className={`w-1 h-1 ${colorClass.replace('text-', 'bg-')} rounded-full animate-pulse`}
              style={{ 
                animationDelay: `${i * 0.15}s`,
                animationDuration: '1s'
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );

  // 全画面表示の場合
  if (fullScreen) {
    return (
      <div className="fixed inset-0 bg-white bg-opacity-95 backdrop-blur-sm flex items-center justify-center z-50">
        <div className="bg-white rounded-xl shadow-xl p-8 max-w-sm w-full mx-4 border border-gray-100">
          {loadingContent}
        </div>
      </div>
    );
  }

  // 通常表示の場合
  return (
    <div className="flex items-center justify-center p-6">
      <div className="bg-white rounded-lg shadow-card p-6 border border-gray-100">
        {loadingContent}
      </div>
    </div>
  );
};

export default Loading;