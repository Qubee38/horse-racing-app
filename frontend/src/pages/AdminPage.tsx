// frontend/src/pages/AdminPage.tsx

import React, { useEffect, useState } from 'react';
import { Settings, Save, RotateCcw, ArrowLeft } from 'lucide-react';
import Header from '../components/common/Header';
import Loading from '../components/common/Loading';
import ErrorMessage from '../components/common/ErrorMessage';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

interface AdminPageProps {
    onBack: () => void; // 追加
  }

interface AICommentaryConfig {
  overwhelming_favorite_gap: number;
  safe_place_bet_threshold: number;
  grade_race_scores: {
    G1: number;
    G2: number;
    G3: number;
  };
  overwhelming_favorite_score: number;
  max_recommended_races: number;
  claude_model: string;
  max_tokens: number;
  system_prompt: string;
}

const AdminPage: React.FC<AdminPageProps> = ({ onBack }) => {
  const [config, setConfig] = useState<AICommentaryConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const loadConfig = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get(`${API_BASE_URL}/admin/ai-commentary/config`);
      setConfig(response.data);
    } catch (err: any) {
      setError('設定の読み込みに失敗しました');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConfig();
  }, []);

  const handleSave = async () => {
    if (!config) return;

    try {
      setSaving(true);
      setError(null);
      setSuccessMessage(null);

      await axios.put(`${API_BASE_URL}/admin/ai-commentary/config`, {
        overwhelming_favorite_gap: config.overwhelming_favorite_gap,
        safe_place_bet_threshold: config.safe_place_bet_threshold,
        grade_race_scores: config.grade_race_scores,
        overwhelming_favorite_score: config.overwhelming_favorite_score,
        max_recommended_races: config.max_recommended_races,
        max_tokens: config.max_tokens
      });

      setSuccessMessage('設定を保存しました');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err: any) {
      setError('設定の保存に失敗しました');
    } finally {
      setSaving(false);
    }
  };

  const handleReset = async () => {
    if (!window.confirm('設定をデフォルトに戻しますか？')) return;

    try {
      setSaving(true);
      setError(null);
      await axios.post(`${API_BASE_URL}/admin/ai-commentary/config/reset`);
      await loadConfig();
      setSuccessMessage('設定をデフォルトに戻しました');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err: any) {
      setError('設定のリセットに失敗しました');
    } finally {
      setSaving(false);
    }
  };

  const handleBack = () => {
    onBack(); // 修正: window.location.href ではなく props の onBack を呼ぶ
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header title="AI解説設定" onHomeClick={handleBack} />
        <div className="p-4 max-w-4xl mx-auto">
          <Loading message="設定を読み込んでいます..." size="large" />
        </div>
      </div>
    );
  }

  if (!config) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Header title="AI解説設定" onHomeClick={handleBack} />
        <div className="p-4 max-w-4xl mx-auto">
          <ErrorMessage message="設定の読み込みに失敗しました" onRetry={loadConfig} />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header title="AI解説設定" onHomeClick={handleBack}>
        <button
          onClick={handleBack}
          className="bg-gray-600 hover:bg-gray-700 text-white py-2 px-3 rounded-lg text-sm font-semibold flex items-center gap-2"
        >
          <ArrowLeft className="w-4 h-4" />
          戻る
        </button>
      </Header>

      <div className="p-4 max-w-4xl mx-auto">
        {/* 成功メッセージ */}
        {successMessage && (
          <div className="mb-4 bg-green-50 border border-green-200 rounded-lg p-4">
            <p className="text-green-800 font-medium">{successMessage}</p>
          </div>
        )}

        {/* エラーメッセージ */}
        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-800 font-medium">{error}</p>
          </div>
        )}

        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="flex items-center mb-6">
            <Settings className="w-6 h-6 text-blue-600 mr-2" />
            <h2 className="text-2xl font-bold text-gray-800">AI解説設定</h2>
          </div>

          <div className="space-y-6">
            {/* 圧倒的本命の判定基準 */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                圧倒的本命の判定基準（1着確率の差分）
              </label>
              <div className="flex items-center gap-4">
                <input
                  type="range"
                  min="5"
                  max="30"
                  step="0.5"
                  value={config.overwhelming_favorite_gap}
                  onChange={(e) => setConfig({
                    ...config,
                    overwhelming_favorite_gap: parseFloat(e.target.value)
                  })}
                  className="flex-1"
                />
                <span className="w-20 text-right font-mono text-lg">
                  {config.overwhelming_favorite_gap.toFixed(1)}%
                </span>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                1位と2位の勝率差がこの値以上の場合、圧倒的本命と判定
              </p>
            </div>

            {/* 鉄板複勝の判定基準 */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                鉄板複勝の判定基準（3着以内確率）
              </label>
              <div className="flex items-center gap-4">
                <input
                  type="range"
                  min="70"
                  max="100"
                  step="1"
                  value={config.safe_place_bet_threshold}
                  onChange={(e) => setConfig({
                    ...config,
                    safe_place_bet_threshold: parseFloat(e.target.value)
                  })}
                  className="flex-1"
                />
                <span className="w-20 text-right font-mono text-lg">
                  {config.safe_place_bet_threshold.toFixed(0)}%
                </span>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                複勝率がこの値以上の場合、鉄板複勝候補と判定
              </p>
            </div>

            {/* 重賞レースのスコア */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-3">
                重賞レースのスコア
              </label>
              <div className="grid grid-cols-3 gap-4">
                {['G1', 'G2', 'G3'].map((grade) => (
                  <div key={grade}>
                    <label className="block text-xs text-gray-600 mb-1">{grade}</label>
                    <input
                      type="number"
                      min="0"
                      max="20"
                      value={config.grade_race_scores[grade as keyof typeof config.grade_race_scores]}
                      onChange={(e) => setConfig({
                        ...config,
                        grade_race_scores: {
                          ...config.grade_race_scores,
                          [grade]: parseInt(e.target.value) || 0
                        }
                      })}
                      className="w-full border border-gray-300 rounded px-3 py-2 text-center font-mono"
                    />
                  </div>
                ))}
              </div>
              <p className="text-xs text-gray-500 mt-1">
                おすすめレース選定時の加算スコア
              </p>
            </div>

            {/* 本命明確スコア */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                本命明確スコア
              </label>
              <div className="flex items-center gap-4">
                <input
                  type="range"
                  min="0"
                  max="10"
                  step="1"
                  value={config.overwhelming_favorite_score}
                  onChange={(e) => setConfig({
                    ...config,
                    overwhelming_favorite_score: parseInt(e.target.value)
                  })}
                  className="flex-1"
                />
                <span className="w-20 text-right font-mono text-lg">
                  {config.overwhelming_favorite_score}
                </span>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                圧倒的本命がいる場合のおすすめレース加算スコア
              </p>
            </div>

            {/* おすすめレース最大数 */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                おすすめレース最大数
              </label>
              <div className="flex items-center gap-4">
                <input
                  type="range"
                  min="1"
                  max="10"
                  step="1"
                  value={config.max_recommended_races}
                  onChange={(e) => setConfig({
                    ...config,
                    max_recommended_races: parseInt(e.target.value)
                  })}
                  className="flex-1"
                />
                <span className="w-20 text-right font-mono text-lg">
                  {config.max_recommended_races}
                </span>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                AI解説で紹介する最大レース数
              </p>
            </div>

            {/* 最大トークン数 */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                最大トークン数
              </label>
              <div className="flex items-center gap-4">
                <input
                  type="range"
                  min="1000"
                  max="4000"
                  step="100"
                  value={config.max_tokens}
                  onChange={(e) => setConfig({
                    ...config,
                    max_tokens: parseInt(e.target.value)
                  })}
                  className="flex-1"
                />
                <span className="w-20 text-right font-mono text-lg">
                  {config.max_tokens}
                </span>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Claude APIの応答最大トークン数（長いほど詳細な解説）
              </p>
            </div>

            {/* モデル情報（読み取り専用） */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                使用モデル
              </label>
              <input
                type="text"
                value={config.claude_model}
                readOnly
                className="w-full border border-gray-300 rounded px-3 py-2 bg-gray-50 text-gray-600"
              />
            </div>
          </div>

          {/* ボタン */}
          <div className="flex justify-between items-center mt-8 pt-6 border-t">
            <button
              onClick={handleReset}
              disabled={saving}
              className="bg-gray-500 hover:bg-gray-600 disabled:bg-gray-300 text-white py-2 px-4 rounded-lg font-semibold flex items-center gap-2 transition-colors"
            >
              <RotateCcw className="w-4 h-4" />
              デフォルトに戻す
            </button>

            <button
              onClick={handleSave}
              disabled={saving}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white py-2 px-6 rounded-lg font-semibold flex items-center gap-2 transition-colors"
            >
              {saving ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  保存中...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4" />
                  設定を保存
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminPage;