/**
 * フォーマット関連のユーティリティ関数
 */

/**
 * オッズをフォーマット
 * @param odds オッズの数値
 * @returns フォーマットされたオッズ文字列 (例: "3.2倍", "---")
 */
export const formatOdds = (odds: number | null | undefined): string => {
    if (odds === null || odds === undefined || isNaN(odds)) {
        return '---';
    }
    
    return `${odds.toFixed(1)}倍`;
    };
    
    /**
     * 確率をフォーマット
     * @param probability 確率の数値（パーセント）
     * @returns フォーマットされた確率文字列 (例: "25.3%", "---")
     */
    export const formatProbability = (probability: number | null | undefined): string => {
    if (probability === null || probability === undefined || isNaN(probability)) {
        return '---';
    }
    
    return `${probability.toFixed(1)}%`;
    };
    
    /**
     * 期待値に応じたCSSクラスを取得
     * @param value 期待値
     * @returns TailwindCSSクラス文字列
     */
    export const getExpectedValueColor = (value: number | null | undefined): string => {
    if (value === null || value === undefined || isNaN(value)) {
        return 'bg-gray-100 text-gray-600';
    }
    
    if (value >= 110) return 'bg-red-100 text-red-800';    // 非常に有望
    if (value >= 100) return 'bg-yellow-100 text-yellow-800'; // やや有望
    return 'bg-gray-100 text-gray-600';                    // 通常
    };
    
    /**
     * 期待値をフォーマット
     * @param value 期待値
     * @returns フォーマットされた期待値文字列 (例: "108.5%", "---")
     */
    export const formatExpectedValue = (value: number | null | undefined): string => {
    if (value === null || value === undefined || isNaN(value)) {
        return '---';
    }
    
    return `${value.toFixed(1)}%`;
    };
    
    /**
     * 数値を3桁区切りでフォーマット
     * @param num 数値
     * @returns フォーマットされた数値文字列 (例: "1,234", "---")
     */
    export const formatNumber = (num: number | null | undefined): string => {
    if (num === null || num === undefined || isNaN(num)) {
        return '---';
    }
    
    return num.toLocaleString();
    };
    
    /**
     * 距離をフォーマット（メートル単位）
     * @param distance 距離（メートル）
     * @returns フォーマットされた距離文字列 (例: "1,400m")
     */
    export const formatDistance = (distance: number | string): string => {
    if (typeof distance === 'string') {
        return distance.includes('m') ? distance : `${distance}m`;
    }
    
    if (typeof distance === 'number') {
        return `${formatNumber(distance)}m`;
    }
    
    return '---';
    };
    
    /**
     * 馬場状態を日本語に変換
     * @param surface 馬場 ("turf", "dirt", "芝", "ダート" など)
     * @returns 日本語の馬場名
     */
    export const formatSurface = (surface: string): string => {
    const surfaceMap: { [key: string]: string } = {
        'turf': '芝',
        'dirt': 'ダート', 
        'artificial': '人工芝',
        '芝': '芝',
        'ダート': 'ダート',
    };
    
    return surfaceMap[surface] || surface;
    };
    
    /**
     * 枠番に応じた背景色を取得（競馬の枠色）
     * @param frameNumber 枠番 (1-8)
     * @returns TailwindCSSクラス文字列
     */
    export const getFrameColor = (frameNumber: number): string => {
    const frameColors: { [key: number]: string } = {
        1: 'bg-white text-black border',      // 白
        2: 'bg-black text-white',             // 黒
        3: 'bg-red-500 text-white',           // 赤
        4: 'bg-blue-500 text-white',          // 青
        5: 'bg-yellow-400 text-black',        // 黄
        6: 'bg-green-500 text-white',         // 緑
        7: 'bg-orange-500 text-white',        // 橙
        8: 'bg-pink-500 text-white',          // 桃
    };
    
    return frameColors[frameNumber] || 'bg-gray-500 text-white';
    };