// frontend/src/components/race/AICommentary.tsx

import React, { useEffect, useState, useCallback } from 'react';
import { getAICommentary } from '../../services/api';
import { RefreshCw } from 'lucide-react';

interface AICommentaryProps {
  date: string;
  onCommentaryLoaded?: (commentary: any) => void;
  cachedCommentary?: any;
}

export const AICommentary: React.FC<AICommentaryProps> = ({ 
  date, 
  onCommentaryLoaded,
  cachedCommentary 
}) => {
  const [commentary, setCommentary] = useState<any>(cachedCommentary || null);
  const [loading, setLoading] = useState(!cachedCommentary);
  const [error, setError] = useState<string | null>(null);

  // 修正: cachedCommentaryを依存関係から削除
  const loadCommentary = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getAICommentary(date);
      setCommentary(data);
      if (onCommentaryLoaded) {
        onCommentaryLoaded(data);
      }
    } catch (err: any) {
      setError(err.message || 'AI解説の取得に失敗しました');
    } finally {
      setLoading(false);
    }
  }, [date, onCommentaryLoaded]); // cachedCommentaryを削除

  // 修正: cachedCommentaryとdateを依存関係に追加
  useEffect(() => {
    // キャッシュがない場合のみ取得
    if (!cachedCommentary && date) {
      loadCommentary();
    }
  }, [cachedCommentary, date, loadCommentary]); // 依存関係を追加

  const handleRegenerate = () => {
    loadCommentary();
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-4">
        <div className="animate-pulse">
          <div className="h-3 bg-gray-200 rounded w-3/4 mb-3"></div>
          <div className="h-3 bg-gray-200 rounded w-full mb-2"></div>
          <div className="h-3 bg-gray-200 rounded w-5/6"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
        <p className="text-yellow-800 text-xs mb-2">{error}</p>
        <button
          onClick={handleRegenerate}
          className="text-yellow-700 hover:text-yellow-900 text-xs underline flex items-center gap-1"
        >
          <RefreshCw className="w-3 h-3" />
          再試行
        </button>
      </div>
    );
  }

  if (!commentary) {
    return null;
  }

  return (
    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg shadow p-4">
      {/* ヘッダー */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center">
          <span className="text-xl mr-2">🤖</span>
          <h2 className="text-base font-bold text-gray-800">
            AI予想解説
          </h2>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-500">powered by Claude</span>
          <button
            onClick={handleRegenerate}
            className="text-gray-500 hover:text-gray-700 transition-colors"
            title="解説を再生成"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* 解説本文 - コンパクトスタイル */}
      <div className="text-xs leading-relaxed">
        <div 
          className="whitespace-pre-wrap text-gray-700"
          style={{ lineHeight: '1.6' }}
          dangerouslySetInnerHTML={{ 
            __html: formatCommentary(commentary.commentary) 
          }}
        />
      </div>

      {/* おすすめレース */}
      {commentary.recommended_races && commentary.recommended_races.length > 0 && (
        <div className="mt-4 pt-3 border-t border-gray-200">
          <h3 className="text-xs font-semibold text-gray-600 mb-2">
            📌 本日のおすすめレース
          </h3>
          <div className="flex flex-wrap gap-2">
            {commentary.recommended_races.map((race: any, idx: number) => (
              <div 
                key={idx}
                className="bg-white px-2 py-1 rounded-full text-xs border border-gray-200"
              >
                <span className="font-semibold">{race.venue}</span>
                {' '}
                {race.race_number}R
                <span className="text-gray-500 ml-1 text-xs">
                  ({race.reasons.join(', ')})
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Markdownライクなフォーマット適用（サイズ調整）
function formatCommentary(text: string): string {
  return text
    .replace(/### (.*)/g, '<h3 class="text-sm font-bold mt-3 mb-1.5">$1</h3>')
    .replace(/## (.*)/g, '<h2 class="text-base font-bold mt-3 mb-2">$1</h2>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br/>');
}