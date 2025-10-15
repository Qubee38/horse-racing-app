#!/usr/bin/env python3
# backend/scripts/run_model_evaluation.py

"""
競馬予測モデル評価スクリプト

使用方法:
    # 基本実行（schedule.jsonから全レース評価）
    python -m scripts.run_model_evaluation
    
    # レースIDを直接指定
    python -m scripts.run_model_evaluation --race-ids 202506040911 202506040912
    
    # 詳細ログ
    python -m scripts.run_model_evaluation --verbose
    
    # データ準備のみ（評価はスキップ）
    python -m scripts.run_model_evaluation --prepare-only
    
    # 条件別分析をスキップ
    python -m scripts.run_model_evaluation --no-conditional
"""

import sys
import logging
import argparse
from pathlib import Path
from typing import List, Optional
import json
import csv
import traceback

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).resolve().parent.parent))

from scripts.model_evaluation.config import EvaluationConfig
from scripts.model_evaluation.race_id_generator import NetkeibaRaceIDGenerator
from scripts.model_evaluation.data_loader import DataLoader
from scripts.model_evaluation.evaluator import Evaluator
from scripts.model_evaluation.reporter import Reporter
from scripts.model_evaluation.analyzer import ConditionalAnalyzer
from scripts.model_evaluation.html_reporter import HTMLReporter


# グローバルロガー
logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False):
    """ログ設定"""
    log_level = logging.DEBUG if verbose else logging.INFO
    
    # コンソールハンドラ
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # ルートロガー設定
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)


def load_race_ids_from_schedule(config: EvaluationConfig) -> List[str]:
    """
    schedule.jsonからレースIDを生成
    
    Parameters
    ----------
    config : EvaluationConfig
        評価設定
    
    Returns
    -------
    List[str]
        レースIDのリスト
    """
    schedule_path = config.get_schedule_json_path()
    
    if not schedule_path.exists():
        logger.error(f"Schedule JSON not found: {schedule_path}")
        logger.error("Please create schedule.json in data/evaluation/schedules/")
        sys.exit(1)
    
    try:
        # JSONファイル読み込み
        with open(schedule_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 年とスケジュールを取得
        year = data.get('year')
        schedule = data.get('schedule')
        
        if not year or not schedule:
            logger.error("Invalid schedule.json format")
            sys.exit(1)
        
        # レースID生成
        generator = NetkeibaRaceIDGenerator(year)
        race_ids = generator.generate_from_schedule(schedule)
        
        logger.info(f"Generated {len(race_ids)} race IDs from schedule.json")
        
        return race_ids
    
    except Exception as e:
        logger.error(f"Failed to load schedule.json: {e}")
        sys.exit(1)


def load_race_ids_from_csv(config: EvaluationConfig) -> List[str]:
    """
    race_ids.csvからレースIDを読み込み
    
    Parameters
    ----------
    config : EvaluationConfig
        評価設定
    
    Returns
    -------
    List[str]
        レースIDのリスト
    """
    csv_path = config.get_race_id_csv_path()
    
    if not csv_path.exists():
        logger.warning(f"Race ID CSV not found: {csv_path}")
        return []
    
    try:
        race_ids = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                race_id = row.get('race_id')
                if race_id:
                    race_ids.append(race_id)
        
        logger.info(f"Loaded {len(race_ids)} race IDs from CSV")
        return race_ids
    
    except Exception as e:
        logger.error(f"Failed to load race IDs from CSV: {e}")
        return []


def progress_callback(current: int, total: int, message: str):
    """進捗表示用コールバック"""
    percentage = (current / total) * 100 if total > 0 else 0
    logger.info(f"[{current}/{total}] ({percentage:.1f}%) {message}")


def main():
    """メイン処理"""
    # コマンドライン引数解析
    parser = argparse.ArgumentParser(
        description='競馬予測モデル評価スクリプト',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 基本実行（schedule.jsonから全レース評価）
  python -m scripts.run_model_evaluation

  # レースIDを直接指定
  python -m scripts.run_model_evaluation --race-ids 202506040911 202506040912

  # 詳細ログ
  python -m scripts.run_model_evaluation --verbose

  # データ準備のみ（評価はスキップ）
  python -m scripts.run_model_evaluation --prepare-only
  
  # 条件別分析をスキップ
  python -m scripts.run_model_evaluation --no-conditional
        """
    )
    
    parser.add_argument(
        '--race-ids',
        nargs='+',
        help='評価対象のレースID（複数指定可）'
    )
    
    parser.add_argument(
        '--prepare-only',
        action='store_true',
        help='データ準備のみ実行（評価はスキップ）'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='詳細ログを出力'
    )
    
    parser.add_argument(
        '--no-scrape-payback',
        action='store_true',
        help='払い戻し情報の自動スクレイピングを無効化'
    )
    
    parser.add_argument(
        '--no-conditional',
        action='store_true',
        help='条件別分析をスキップ'
    )
    
    args = parser.parse_args()
    
    # ログ設定
    setup_logging(args.verbose)
    
    logger.info("=" * 80)
    logger.info("Model Evaluation Script Started")
    logger.info("=" * 80)
    
    # 設定初期化
    config = EvaluationConfig()
    
    # 払い戻しスクレイピング設定
    if args.no_scrape_payback:
        config.SCRAPE_MISSING_PAYBACK = False
    
    # 設定検証
    if not config.validate_config():
        logger.error("Configuration validation failed")
        sys.exit(1)
    
    # 必要なディレクトリ作成
    config.ensure_directories()
    
    # 設定内容表示
    if args.verbose:
        config.print_config()
    
    # レースID取得
    if args.race_ids:
        # コマンドライン引数から
        race_ids = args.race_ids
        logger.info(f"Using {len(race_ids)} race IDs from command line")
    else:
        # CSVファイルから読み込み、なければschedule.jsonから生成
        race_ids = load_race_ids_from_csv(config)
        
        if not race_ids:
            logger.info("No race IDs found in CSV, generating from schedule.json...")
            race_ids = load_race_ids_from_schedule(config)
    
    if not race_ids:
        logger.error("No race IDs to evaluate")
        sys.exit(1)
    
    logger.info(f"Total race IDs to evaluate: {len(race_ids)}")
    
    try:
        # DataLoader初期化
        logger.info("\nInitializing DataLoader...")
        loader = DataLoader(config)
        
        # ========================================
        # Phase 0: データ準備
        # ========================================
        logger.info("\n" + "=" * 80)
        logger.info("Phase 0: Data Preparation")
        logger.info("=" * 80)
        
        valid_race_ids = loader.prepare_evaluation_data(
            race_ids,
            progress_callback=progress_callback
        )
        
        logger.info(f"\nData preparation completed: {len(valid_race_ids)}/{len(race_ids)} races ready")
        
        if len(valid_race_ids) == 0:
            logger.error("No valid race data prepared")
            sys.exit(1)
        
        # データ準備のみの場合はここで終了
        if args.prepare_only:
            logger.info("\n--prepare-only specified, skipping evaluation")
            logger.info("=" * 80)
            logger.info("Script Completed Successfully")
            logger.info("=" * 80)
            return
        
        # ========================================
        # Phase 1: データ読み込み・予測実行
        # ========================================
        logger.info("\n" + "=" * 80)
        logger.info("Phase 1: Data Loading & Prediction")
        logger.info("=" * 80)
        
        race_data_list = loader.get_all_race_data(
            valid_race_ids,
            progress_callback=progress_callback
        )
        
        logger.info(f"\nData loading completed: {len(race_data_list)} races loaded")
        
        if len(race_data_list) == 0:
            logger.error("No race data loaded")
            sys.exit(1)
        
        # 統計情報
        stats = loader.get_statistics(race_data_list)
        logger.info("\nData Statistics:")
        logger.info(f"  Total races: {stats['total_races']}")
        logger.info(f"  Total horses: {stats['total_horses']}")
        logger.info(f"  Races with payback: {stats['races_with_payback']}")
        logger.info(f"  Average horses per race: {stats['average_horses_per_race']:.1f}")
        
        # ========================================
        # Phase 2: 全体評価
        # ========================================
        logger.info("\n" + "=" * 80)
        logger.info("Phase 2: Overall Strategy Evaluation")
        logger.info("=" * 80)
        
        evaluator = Evaluator(config)
        results = evaluator.evaluate_all_strategies(race_data_list)
        
        logger.info(f"\nEvaluation completed: {len(results)} strategies")
        
        # ========================================
        # Phase 3: 条件別分析
        # ========================================
        venue_results = None
        grade_results = None
        track_results = None
        distance_results = None
        condition_results = None
        
        if config.ENABLE_CONDITIONAL_ANALYSIS and not args.no_conditional:
            logger.info("\n" + "=" * 80)
            logger.info("Phase 3: Conditional Analysis")
            logger.info("=" * 80)
            
            # 条件別分析器初期化
            analyzer = ConditionalAnalyzer(config, evaluator)
            
            try:
                # 1. 競馬場別分析
                logger.info("\n--- 1/5: Venue Analysis ---")
                venue_results = analyzer.analyze_by_venue(race_data_list)
                if venue_results:
                    venue_stats = analyzer.get_statistics(venue_results)
                    logger.info(f"✓ Analyzed {venue_stats['total_conditions']} venues, {venue_stats['total_races']} races")
                    logger.info(f"  Venues: {', '.join(venue_stats['conditions'])}")
                
                # 2. グレード別分析
                logger.info("\n--- 2/5: Grade Analysis ---")
                grade_results = analyzer.analyze_by_grade(race_data_list)
                if grade_results:
                    grade_stats = analyzer.get_statistics(grade_results)
                    logger.info(f"✓ Analyzed {grade_stats['total_conditions']} grades, {grade_stats['total_races']} races")
                    logger.info(f"  Grades: {', '.join(grade_stats['conditions'])}")
                
                # 3. トラック別分析
                logger.info("\n--- 3/5: Track Type Analysis ---")
                track_results = analyzer.analyze_by_track_type(race_data_list)
                if track_results:
                    track_stats = analyzer.get_statistics(track_results)
                    logger.info(f"✓ Analyzed {track_stats['total_conditions']} track types, {track_stats['total_races']} races")
                    logger.info(f"  Track types: {', '.join(track_stats['conditions'])}")
                
                # 4. 距離別分析
                logger.info("\n--- 4/5: Distance Analysis ---")
                distance_results = analyzer.analyze_by_distance(race_data_list)
                if distance_results:
                    distance_stats = analyzer.get_statistics(distance_results)
                    logger.info(f"✓ Analyzed {distance_stats['total_conditions']} distance ranges, {distance_stats['total_races']} races")
                    logger.info(f"  Distance ranges: {', '.join(distance_stats['conditions'])}")
                
                # 5. 馬場状態別分析
                logger.info("\n--- 5/5: Track Condition Analysis ---")
                condition_results = analyzer.analyze_by_track_condition(race_data_list)
                if condition_results:
                    condition_stats = analyzer.get_statistics(condition_results)
                    logger.info(f"✓ Analyzed {condition_stats['total_conditions']} track conditions, {condition_stats['total_races']} races")
                    logger.info(f"  Track conditions: {', '.join(condition_stats['conditions'])}")
                else:
                    logger.info("⚠ No track condition data available")
                
                logger.info("\n✓ Conditional analysis completed")
            
            except Exception as e:
                logger.error(f"✗ Error in conditional analysis: {e}")
                logger.error(traceback.format_exc())
                logger.warning("Continuing with report generation...")
        else:
            logger.info("\n" + "=" * 80)
            logger.info("Phase 3: Conditional Analysis SKIPPED")
            logger.info("=" * 80)
            if args.no_conditional:
                logger.info("  Reason: --no-conditional flag specified")
            else:
                logger.info("  Reason: ENABLE_CONDITIONAL_ANALYSIS = False in config.py")
        
        # ========================================
        # Phase 4: レポート生成
        # ========================================
        logger.info("\n" + "=" * 80)
        logger.info("Phase 4: Report Generation")
        logger.info("=" * 80)
        
        reporter = Reporter(config)
        
        # コンソール出力
        reporter.print_summary(results)
        
        # CSVレポート生成
        try:
            report_paths = reporter.generate_all_reports(
                overall_results=results,
                venue_results=venue_results,
                grade_results=grade_results,
                track_results=track_results,
                distance_results=distance_results,
                condition_results=condition_results
            )
            
            logger.info("\n" + "=" * 80)
            logger.info("Generated Reports:")
            logger.info("=" * 80)
            for report_type, path in report_paths.items():
                logger.info(f"  ✓ {report_type}: {path.name}")
            
            logger.info(f"\nAll reports saved to: {config.REPORT_DIR}")

            # ========================================
            # HTMLレポート生成（新規追加）
            # ========================================
            logger.info("\n" + "=" * 80)
            logger.info("Generating HTML Report")
            logger.info("=" * 80)
            
            html_reporter = HTMLReporter(config)
            html_path = html_reporter.generate_html_report(
                results,
                venue_results=venue_results,
                grade_results=grade_results,
                track_results=track_results,
                distance_results=distance_results,
                condition_results=condition_results
            )
            
            logger.info(f"\n✓ HTML report generated: {html_path.name}")
            logger.info(f"  Open with: open {html_path}")
        
        except Exception as e:
            logger.error(f"✗ Error generating reports: {e}")
            logger.error(traceback.format_exc())
            sys.exit(1)
        
        # ========================================
        # 完了
        # ========================================
        logger.info("\n" + "=" * 80)
        logger.info("Script Completed Successfully")
        logger.info("=" * 80)
    
    except KeyboardInterrupt:
        logger.warning("\n\n✗ Script interrupted by user")
        sys.exit(1)
    
    except Exception as e:
        logger.error(f"\n\n✗ Script failed with error: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()