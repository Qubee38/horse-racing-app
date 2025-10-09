/**
 * アプリケーション全体で使用する定数定義
 */

// API関連
export const API_ENDPOINTS = {
    RACES: '/races',
    HORSES: '/horses', 
    PREDICTIONS: '/predictions',
    HEALTH: '/health',
  } as const;
  
  // 日付フォーマット
  export const DATE_FORMATS = {
    API: 'YYYY-MM-DD',
    DISPLAY: 'YYYY年MM月DD日',
    TIME: 'HH:mm',
  } as const;
  
  // 競馬場一覧
  export const VENUES = [
    '東京', '中山', '京都', '阪神', '中京', '新潟',
    '小倉', '札幌', '函館', '福島'
  ] as const;
  
  // 馬場種類
  export const SURFACES = {
    TURF: '芝',
    DIRT: 'ダート',
    ARTIFICIAL: '人工芝',
  } as const;
  
  // 距離カテゴリ
  export const DISTANCE_CATEGORIES = {
    SPRINT: { min: 1000, max: 1400, label: '短距離' },
    MILE: { min: 1401, max: 1899, label: 'マイル' },
    INTERMEDIATE: { min: 1900, max: 2100, label: '中距離' },
    LONG: { min: 2101, max: 3600, label: '長距離' },
  } as const;
  
  // 期待値カテゴリ
  export const EXPECTED_VALUE_CATEGORIES = {
    VERY_PROMISING: { min: 110, label: '非常に有望', color: 'bg-red-100 text-red-800' },
    PROMISING: { min: 100, label: 'やや有望', color: 'bg-yellow-100 text-yellow-800' },
    NORMAL: { min: 0, label: '通常', color: 'bg-gray-100 text-gray-600' },
  } as const;
  
  // ローディング・エラーメッセージ
  export const MESSAGES = {
    LOADING: {
      RACES: 'レース情報を読み込んでいます...',
      HORSES: '出走馬情報を読み込んでいます...',
      PREDICTION: '予測を実行しています...',
      DEFAULT: '読み込み中...',
    },
    ERROR: {
      NETWORK: 'ネットワークエラーが発生しました',
      SERVER: 'サーバーエラーが発生しました', 
      NOT_FOUND: '情報が見つかりませんでした',
      PREDICTION_FAILED: '予測の実行に失敗しました',
      DEFAULT: 'エラーが発生しました',
    },
    SUCCESS: {
      PREDICTION_COMPLETED: '予測が完了しました',
      DATA_UPDATED: 'データを更新しました',
    },
  } as const;
  
  // ページネーション
  export const PAGINATION = {
    DEFAULT_PAGE_SIZE: 20,
    PAGE_SIZE_OPTIONS: [10, 20, 50, 100],
  } as const;
  
  // ローカルストレージキー
  export const STORAGE_KEYS = {
    LAST_SELECTED_DATE: 'lastSelectedDate',
    USER_PREFERENCES: 'userPreferences', 
    PREDICTION_HISTORY: 'predictionHistory',
  } as const;