// frontend/src/types/api.ts (修正版)

// 基本的なAPIレスポンス型
export interface ApiError {
    detail: string;
    status_code?: number;
  }
  
  // システム関連
  export interface HealthResponse {
    status: string;
    database: string;
    predictor?: string;
  }
  
  // レース関連の型定義
  export interface Race {
    id: number;
    venue: string;
    race_name: string;
    race_number: number;
    race_date: string;
    start_time: string;
    distance: number;
    surface: string;
    grade?: string;
    horse_count: number;
    netkeiba_race_id?: string;
    created_at?: string;
    updated_at?: string;
  }
  
  export interface Horse {
    id: number;
    race_id: number;
    name: string;
    jockey: string;
    frame_number: number;
    horse_number: number;
    odds?: number;
    popularity?: number;
    weight?: number;
    weight_change?: number;
    handicap?: number;
    created_at?: string;
    updated_at?: string;
    
    // 予測結果（予測実行後に付与される）
    win_probability?: number;
    place_probability?: number;
    expected_value?: number;
    confidence_score?: number;
  }
  
  // API レスポンス型
  export type RacesResponse = Race[];
  export type HorsesResponse = Horse[];
  
  // 予測関連の型定義（修正版）
  export interface PredictionRequest {
    date: string;
    method?: "netkeiba_scraping" | "database_only";
  }
  
  export interface PredictionResponse {
    success: boolean;
    message: string;
    batch_id: number;        // 追加
    target_date: string;
    method: string;
    status: string;
    found_races?: number;    // 追加
  }
  
  // 単一レース予測関連
  export interface SingleRacePredictionRequest {
    race_id: string;
  }
  
  export interface SingleRacePredictionResponse {
    success: boolean;
    race_id: string;
    race_info: {
      race_name: string;
      location: string;
      date: string;
      distance: string;
      track_type: number;
      [key: string]: any;
    };
    predictions: Array<{
      horse_id: number;
      horse_name: string;
      jockey: string;
      horse_number: number;
      frame_number: number;
      odds: number;
      win_probability: number;
      place_probability: number;
      expected_value: number;
      confidence_score: number;
    }>;
    model_type: string;
    message: string;
  }
  
  // バッチ処理状況
  export interface BatchStatus {
    batch_id: number;
    target_date: string;
    status: "RUNNING" | "COMPLETED" | "FAILED";
    total_races: number;
    total_horses: number;
    completed_predictions: number;
    failed_predictions: number;
    start_time: string;
    end_time?: string;
    processing_time_seconds?: number;
    error_message?: string;
  }
  
  // モデル情報
  export interface ModelInfo {
    status: "loaded" | "not_loaded" | "failed_to_load";
    model_type?: "new" | "legacy";
    models_path: string;
    feature_count?: number;
    model_files?: {
      win_model?: string;
      place_model?: string;
      legacy_model?: string;
    };
    feature_names_sample?: string[];
    loaded_at?: string;
    feature_engineering?: {
      total_features: number;
      model_input_features: number;
      jockey_data_loaded: boolean;
      time_data_loaded: boolean;
    };
    message?: string;
  }

// 選択レース予測リクエスト
export interface SelectedRacesPredictionRequest {
  date: string;
  race_ids: string[];
}

// 選択レース予測レスポンス
export interface SelectedRacesPredictionResponse {
  success: boolean;
  message: string;
  batch_id: number;
  target_date: string;
  selected_race_count: number;
  race_ids: string[];
  status: string;
}

// レース選択用の情報
export interface RaceSelectionInfo {
  netkeiba_race_id: string;
  race_number: number;
  race_name: string;
  venue: string;
  start_time: string;
  distance: number;
}

// 馬結果情報
export interface HorseResult {
  id: number;
  horse_id: number | null;
  horse_name: string | null;
  horse_number: number;
  finish_position: number | null;
  popularity: number | null;
}

// 払い戻し情報
export interface Payout {
  id: number;
  bet_type: string | null;        // "win", "place"
  bet_type_name: string | null;   // "単勝", "複勝"
  winning_numbers: string;
  payout_amount: number;
}

// レース結果レスポンス
export interface RaceResultResponse {
  id: number;
  race_id: number;
  race_status: string;  // "completed", "cancelled", "partial_data"
  result_fetched_at: string;
  horse_results: HorseResult[];
  payouts: Payout[];
}

// レース結果サマリーレスポンス
export interface RaceResultSummaryResponse {
  race_status: string;
  result_fetched_at: string;
  horse_results: Array<{
    horse_id: number | null;
    horse_name: string | null;
    horse_number: number | null;
    finish_position: number | null;
    popularity: number | null;
  }>;
  payouts: Array<{
    bet_type_name: string | null;
    winning_numbers: string;
    payout_amount: number;
  }>;
}

// レース結果存在確認レスポンス
export interface RaceResultExistsResponse {
  exists: boolean;
  race_id: number;
}

// レース結果取得リクエストレスポンス
export interface FetchRaceResultResponse {
  status: "processing" | "completed" | "error";
  message: string;
  race_id: number;
  already_exists?: boolean;
}

// frontend/src/types/api.ts の統計関連型定義（Phase1修正版）

// ========================================
// 統計関連の型定義
// ========================================

export interface PeriodInfo {
  start_date: string;
  end_date: string;
  total_days: number;
}

export interface BetTypeStats {
  hit_horses: number;      // 的中馬数
  total_horses: number;    // 対象馬数
  hits: number;            // 的中数（後方互換性）
  accuracy: number;        // 的中率（%）
  total_payout: number;    // 合計配当（円）
  average_payout: number;  // 平均配当（円）
  roi: number;             // 回収率（%）
}

export interface RankBasedStats {
  total_races: number;
  win: BetTypeStats;
  place: BetTypeStats;
}

export interface ProbabilityBasedBetStats {
  threshold: number;
  recommended_races: number;
  recommended_horses: number;
  hit_horses: number;      // 的中馬数
  hits: number;            // 後方互換性
  accuracy: number;
  average_probability: number;
  total_payout: number;    // 合計配当（円）
  average_payout: number;
  roi: number;
  no_recommendation_races: number;
}

export interface ProbabilityBasedStats {
  win: ProbabilityBasedBetStats;
  place: ProbabilityBasedBetStats;
}

export interface ProbabilityRangeStats {
  range: string;
  races: number;
  hits: number;
  accuracy: number;
  avg_payout: number;
  roi: number;
}

export interface ProbabilityBreakdown {
  win: ProbabilityRangeStats[];
  place: ProbabilityRangeStats[];
}

export interface VenueStats {
  venue: string;
  by_rank: RankBasedStats;
  by_probability: ProbabilityBasedStats;
}

export interface GradeStats {
  grade: string;
  by_rank: RankBasedStats;
  by_probability: ProbabilityBasedStats;
}

export interface TrackTypeStats {
  track_type: string;
  by_rank: RankBasedStats;
  by_probability: ProbabilityBasedStats;
}

export interface DistanceRangeStats {
  distance_range: string;
  by_rank: RankBasedStats;
  by_probability: ProbabilityBasedStats;
}

export interface TrackConditionStats {
  track_condition: string;
  by_rank: RankBasedStats;
  by_probability: ProbabilityBasedStats;
}

export interface StatisticsSummaryResponse {
  period: PeriodInfo;
  by_rank: RankBasedStats;
  by_probability: ProbabilityBasedStats;
  probability_breakdown: ProbabilityBreakdown;
  by_venue: VenueStats[];
  by_grade: GradeStats[];
  by_track_type: TrackTypeStats[];
  by_distance: DistanceRangeStats[];
  by_track_condition: TrackConditionStats[];  // 新規追加
}

// ========================================
// レース結果一括取得関連の型定義
// ========================================

export interface BatchFetchRaceResult {
  race_id: number;
  race_number: number;
  race_name: string;
  status: "success" | "skipped" | "failed";
  message: string;
}

export interface BatchFetchRaceResultsResponse {
  date: string;
  total_races: number;
  target_races: number;
  skipped_races: number;
  results: BatchFetchRaceResult[];
  summary: {
    success: number;
    skipped: number;
    failed: number;
  };
}