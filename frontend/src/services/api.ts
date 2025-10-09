// frontend/src/services/api.ts (Warning修正版)
import axios, { AxiosResponse, AxiosError } from 'axios';
import { 
  Race, 
  Horse, 
  RacesResponse, 
  HorsesResponse, 
  HealthResponse,
  PredictionRequest,
  PredictionResponse,
  SingleRacePredictionRequest,
  SingleRacePredictionResponse,
  BatchStatus,
  ModelInfo,
  SelectedRacesPredictionResponse,
  SelectedRacesPredictionRequest,
  RaceResultResponse,
  RaceResultSummaryResponse,
  StatisticsSummaryResponse,
  BatchFetchRaceResultsResponse
  // ApiError 削除 - 未使用のため
} from '../types/api';

// API設定
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';
const API_TIMEOUT = 60000; // デフォルト60秒
const AI_COMMENTARY_TIMEOUT = 180000; // AI解説専用: 180秒（3分）

/**
 * Axiosクライアントの設定
 */
const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

/**
 * リクエストインターセプター
 */
apiClient.interceptors.request.use(
  (config) => {
    const method = config.method?.toUpperCase() || 'GET';
    const url = config.url || '';
    console.log(`🚀 API Request: ${method} ${url}`);
    
    if (config.data) {
      console.log('📤 Request Data:', config.data);
    }
    
    return config;
  },
  (error) => {
    console.error('❌ Request Error:', error);
    return Promise.reject(error);
  }
);

/**
 * レスポンスインターセプター
 */
apiClient.interceptors.response.use(
  (response) => {
    const method = response.config.method?.toUpperCase() || 'GET';
    const url = response.config.url || '';
    const status = response.status;
    console.log(`✅ API Response: ${method} ${url} (${status})`);
    
    return response;
  },
  (error: AxiosError) => {
    const method = error.config?.method?.toUpperCase() || 'GET';
    const url = error.config?.url || '';
    const status = error.response?.status || 'No Response';
    console.error(`❌ API Error: ${method} ${url} (${status})`);
    
    if (error.response?.data) {
      console.error('📥 Error Data:', error.response.data);
    }
    
    return Promise.reject(error);
  }
);

// frontend/src/services/api.ts の raceService 部分のみ修正版

/**
 * レース関連のAPIサービス（修正版）
 */
export const raceService = {
  /**
   * レースデータが存在する開催日一覧を取得（レース数付き）
   */
  getAvailableRaceDates: async (limit: number = 30, includeCount: boolean = true): Promise<{
    dates: Array<{ date: string; race_count: number }>;
    total_count: number;
  }> => {
    try {
      const response = await apiClient.get(
        `/races/available-dates?limit=${limit}&include_count=${includeCount}`
      );
      
      if (response.data.success) {
        // レース数付きの場合
        if (includeCount && Array.isArray(response.data.dates) && response.data.dates.length > 0) {
          const firstItem = response.data.dates[0];
          
          if (typeof firstItem === 'object' && 'date' in firstItem && 'race_count' in firstItem) {
            // 正しいフォーマット
            return {
              dates: response.data.dates,
              total_count: response.data.total_count
            };
          } else {
            // 文字列配列の場合（フォールバック）
            const datesWithZeroCount = response.data.dates.map((date: string) => ({
              date,
              race_count: 0
            }));
            return {
              dates: datesWithZeroCount,
              total_count: response.data.total_count
            };
          }
        } else {
          // レース数なしの場合（文字列配列）
          const datesWithZeroCount = response.data.dates.map((date: string) => ({
            date,
            race_count: 0
          }));
          return {
            dates: datesWithZeroCount,
            total_count: response.data.total_count
          };
        }
      } else {
        throw new Error('Failed to get available race dates');
      }
    } catch (error: any) {
      console.error('Error fetching available race dates:', error);
      throw new Error(error.response?.data?.detail || 'レース開催日の取得に失敗しました');
    }
  },

  /**
   * 指定日のレース一覧を取得
   */
  getRacesByDate: async (date: string): Promise<Race[]> => {
    try {
      const response: AxiosResponse<RacesResponse> = await apiClient.get(`/races/${date}`);
      return response.data;
    } catch (error: any) {
      console.error('Error fetching races:', error);
      throw new Error(error.response?.data?.detail || 'レース情報の取得に失敗しました');
    }
  },

  /**
   * Netkeibaから指定日のレース一覧を取得（スクレイピング）
   */
  getNetkeibaRacesForDate: async (date: string): Promise<{
    success: boolean;
    date: string;
    races: Array<{
      netkeiba_race_id: string;
      venue: string;
      race_number: number;
      race_name: string;
      start_time: string;
      distance: number;
      surface: string;
      url: string;
    }>;
    total_count: number;
  }> => {
    try {
      const response = await apiClient.get(`/races/netkeiba/${date}`);
      return response.data;
    } catch (error: any) {
      console.error('Error fetching Netkeiba races:', error);
      throw new Error(error.response?.data?.detail || 'Netkeibaからのレース取得に失敗しました');
    }
  },

  /**
   * レースの出走馬一覧を取得
   */
  getRaceHorses: async (raceId: number): Promise<Horse[]> => {
    try {
      const response: AxiosResponse<HorsesResponse> = await apiClient.get(`/races/${raceId}/horses`);
      return response.data;
    } catch (error: any) {
      console.error('Error fetching race horses:', error);
      throw new Error(error.response?.data?.detail || '出走馬情報の取得に失敗しました');
    }
  },

  /**
   * レース詳細情報を取得（レース + 出走馬）
   */
  getRaceDetail: async (raceId: number): Promise<{ race: Race; horses: Horse[] }> => {
    try {
      const [raceResponse, horsesResponse] = await Promise.all([
        apiClient.get(`/races/${raceId}`),
        apiClient.get(`/races/${raceId}/horses`)
      ]);
      
      return {
        race: raceResponse.data,
        horses: horsesResponse.data
      };
    } catch (error: any) {
      console.error('Error fetching race detail:', error);
      throw new Error(error.response?.data?.detail || 'レース詳細情報の取得に失敗しました');
    }
  }
};

/**
 * 予測関連のAPIサービス
 */
export const predictionService = {
  /**
   * 日別予測を実行（従来のエンドポイント）
   */
  executePrediction: async (request: PredictionRequest): Promise<PredictionResponse> => {
    try {
      const response: AxiosResponse<PredictionResponse> = await apiClient.post('/predictions/execute', request);
      return response.data;
    } catch (error: any) {
      console.error('Error executing prediction:', error);
      throw new Error(error.response?.data?.detail || '予測の実行に失敗しました');
    }
  },

  /**
   * 単一レース予測を実行（新しいエンドポイント）
   */
  executeSingleRacePrediction: async (raceId: string): Promise<SingleRacePredictionResponse> => {
    try {
      const requestData: SingleRacePredictionRequest = { race_id: raceId };
      const response: AxiosResponse<SingleRacePredictionResponse> = await apiClient.post('/predictions/execute-race', requestData);
      return response.data;
    } catch (error: any) {
      console.error('Error executing single race prediction:', error);
      throw new Error(error.response?.data?.detail || 'レース予測の実行に失敗しました');
    }
  },

  /**
   * 予測実行状況を確認
   */
  getPredictionStatus: async (batchId: number): Promise<BatchStatus> => {
    try {
      const response: AxiosResponse<BatchStatus> = await apiClient.get(`/predictions/status/${batchId}`);
      return response.data;
    } catch (error: any) {
      console.error('Error fetching prediction status:', error);
      throw new Error(error.response?.data?.detail || '予測状況の取得に失敗しました');
    }
  },

  /**
   * モデル情報を取得
   */
  getModelInfo: async (): Promise<ModelInfo> => {
    try {
      const response: AxiosResponse<ModelInfo> = await apiClient.get('/predictions/model/info');
      return response.data;
    } catch (error: any) {
      console.error('Error fetching model info:', error);
      throw new Error(error.response?.data?.detail || 'モデル情報の取得に失敗しました');
    }
  },

  /**
   * 選択された複数レースの予測を実行
   */
  executeSelectedRacesPrediction: async (
    date: string, 
    raceIds: string[]
  ): Promise<SelectedRacesPredictionResponse> => {
    try {
      const requestData: SelectedRacesPredictionRequest = { 
        date, 
        race_ids: raceIds 
      };
      const response: AxiosResponse<SelectedRacesPredictionResponse> = 
        await apiClient.post('/predictions/execute-selected-races', requestData);
      return response.data;
    } catch (error: any) {
      console.error('Error executing selected races prediction:', error);
      throw new Error(error.response?.data?.detail || '選択レース予測の実行に失敗しました');
    }
  },
};

/**
 * システム関連のAPIサービス
 */
export const systemService = {
  /**
   * ヘルスチェック
   */
  healthCheck: async (): Promise<HealthResponse> => {
    try {
      const response: AxiosResponse<HealthResponse> = await apiClient.get('/health', { 
        baseURL: 'http://localhost:8000' // healthエンドポイントは/apiプレフィックス無し
      });
      return response.data;
    } catch (error: any) {
      console.error('Health check failed:', error);
      throw new Error('サーバーとの接続に失敗しました');
    }
  }
};

/**
 * AI解説を取得（タイムアウト延長版）
 */
export const getAICommentary = async (date: string): Promise<{
  date: string;
  commentary: string;
  recommended_races: Array<{
    race_id: number;
    race_name: string;
    venue: string;
    race_number: number;
    score: number;
    reasons: string[];
  }>;
  highlights_count: number;
  model_used: string;
  config_used: {
    overwhelming_favorite_gap: number;
    safe_place_bet_threshold: number;
    max_recommended_races: number;
  };
}> => {
  try {
    // タイムアウトを180秒に延長
    const response = await apiClient.get(`/races/${date}/ai-commentary`, {
      timeout: AI_COMMENTARY_TIMEOUT
    });
    return response.data;
  } catch (error: any) {
    console.error('Error fetching AI commentary:', error);
    
    // タイムアウトエラーの場合のメッセージを改善
    if (error.code === 'ECONNABORTED') {
      throw new Error('AI解説の生成に時間がかかりすぎました。レース数が多い場合は時間をおいて再試行してください。');
    }
    
    throw new Error(error.response?.data?.detail || 'AI解説の取得に失敗しました');
  }
};

/**
 * レース結果関連のAPIサービス（新規追加）
 */
export const raceResultService = {
  /**
   * レース結果が保存済みか確認
   */
  checkResultExists: async (raceId: number): Promise<boolean> => {
    try {
      const response = await apiClient.get(`/race-results/exists/${raceId}`);
      return response.data.exists;
    } catch (error: any) {
      console.error('Error checking race result existence:', error);
      throw new Error(error.response?.data?.detail || 'レース結果の確認に失敗しました');
    }
  },

  /**
   * レース結果を取得してDBに保存（バックグラウンド処理）
   */
  fetchRaceResult: async (raceId: number): Promise<{
    status: string;
    message: string;
    race_id: number;
    already_exists?: boolean;
  }> => {
    try {
      const response = await apiClient.post(`/race-results/fetch/${raceId}`);
      return response.data;
    } catch (error: any) {
      console.error('Error fetching race result:', error);
      throw new Error(error.response?.data?.detail || 'レース結果の取得に失敗しました');
    }
  },

  /**
   * 保存済みレース結果を取得
   */
  getRaceResult: async (raceId: number): Promise<RaceResultResponse | null> => {
    try {
      const response = await apiClient.get(`/race-results/${raceId}`);
      return response.data;
    } catch (error: any) {
      console.error('Error getting race result:', error);
      
      // 404の場合はnullを返す（結果が存在しない）
      if (error.response?.status === 404) {
        return null;
      }
      
      throw new Error(error.response?.data?.detail || 'レース結果の取得に失敗しました');
    }
  },

  /**
   * レース結果サマリーを取得
   */
  getRaceResultSummary: async (raceId: number): Promise<RaceResultSummaryResponse | null> => {
    try {
      const response = await apiClient.get(`/race-results/summary/${raceId}`);
      return response.data;
    } catch (error: any) {
      console.error('Error getting race result summary:', error);
      
      // 404の場合はnullを返す
      if (error.response?.status === 404) {
        return null;
      }
      
      throw new Error(error.response?.data?.detail || 'レース結果サマリーの取得に失敗しました');
    }
  },
  /**
   * 指定日のレース結果を一括取得（タイムアウト延長版）
   */
  batchFetchRaceResults: async (date: string): Promise<BatchFetchRaceResultsResponse> => {
    try {
      // タイムアウトを300秒（5分）に延長
      const response = await apiClient.post(`/race-results/batch-fetch/${date}`, {}, {
        timeout: 300000  // 300秒 = 5分
      });
      return response.data;
    } catch (error: any) {
      console.error('Error batch fetching race results:', error);
      throw new Error(error.response?.data?.detail || 'レース結果の一括取得に失敗しました');
    }
  }
};

// ========================================
// 統計API
// ========================================

export const statisticsService = {
  /**
   * 統計サマリーを取得
   */
  getSummary: async (params?: {
    start_date?: string;
    end_date?: string;
    win_threshold?: number;
    place_threshold?: number;
  }): Promise<StatisticsSummaryResponse> => {
    const response = await apiClient.get('/statistics/summary', { params });
    return response.data;
  },

  /**
   * デフォルト期間（過去30日）の統計を取得
   */
  getDefaultSummary: async (): Promise<StatisticsSummaryResponse> => {
    const response = await apiClient.get('/statistics/summary', {
      params: {
        win_threshold: 80.0,
        place_threshold: 85.0
      }
    });
    return response.data;
  }
};

// ========================================
// レース管理API（削除・再取得）
// ========================================

/**
 * レース削除
 */
export const deleteRace = async (raceId: number): Promise<{ 
  success: boolean; 
  message: string;
  deleted_race_id: number;
  race_name: string;
  race_date: string;
}> => {
  try {
    const response = await apiClient.delete(`/races/${raceId}`);
    return response.data;
  } catch (error: any) {
    console.error('Error deleting race:', error);
    throw new Error(error.response?.data?.detail || 'レース削除に失敗しました');
  }
};

/**
 * レース結果再取得
 */
export const refetchRaceResult = async (raceId: number): Promise<{ 
  status: string; 
  message: string;
  race_id: number;
}> => {
  try {
    const response = await apiClient.put(`/race-results/refetch/${raceId}`);
    return response.data;
  } catch (error: any) {
    console.error('Error refetching race result:', error);
    throw new Error(error.response?.data?.detail || '結果再取得に失敗しました');
  }
};

// デフォルトエクスポート
export default apiClient;