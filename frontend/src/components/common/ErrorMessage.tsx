import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

// ErrorMessageコンポーネントのプロパティ型定義
interface ErrorMessageProps {
  message: string;              // エラーメッセージ
  onRetry?: () => void;        // リトライボタンがクリックされた時の処理
  showRetryButton?: boolean;   // リトライボタンの表示/非表示
}

/**
 * エラーメッセージ表示コンポーネント
 * - エラーメッセージの統一表示
 * - オプションでリトライボタン
 */
const ErrorMessage: React.FC<ErrorMessageProps> = ({ 
  message, 
  onRetry, 
  showRetryButton = true 
}) => {
  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4 m-4">
      <div className="flex items-center gap-3">
        {/* エラーアイコン */}
        <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
        
        <div className="flex-1">
          {/* エラーメッセージ */}
          <p className="text-red-700 text-sm">{message}</p>
          
          {/* リトライボタン（条件付きで表示） */}
          {showRetryButton && onRetry && (
            <button
              onClick={onRetry}
              className="mt-2 flex items-center gap-2 text-sm text-red-600 hover:text-red-700 font-medium"
            >
              <RefreshCw className="w-4 h-4" />
              再試行
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ErrorMessage;
