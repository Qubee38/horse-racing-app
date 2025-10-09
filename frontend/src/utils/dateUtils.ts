/**
 * 日付関連のユーティリティ関数
 */

/**
 * 日付文字列を日本語形式でフォーマット
 * @param dateString YYYY-MM-DD形式の日付文字列
 * @returns フォーマットされた日付文字列 (例: "2025年9月22日(月)")
 */
export const formatDate = (dateString: string): string => {
try {
    const date = new Date(dateString);
    
    // 無効な日付をチェック
    if (isNaN(date.getTime())) {
    return dateString; // 元の文字列を返す
    }
    
    return date.toLocaleDateString('ja-JP', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    weekday: 'short'
    });
} catch (error) {
    console.error('Date formatting error:', error);
    return dateString;
}
};

/**
 * Date オブジェクトをAPI用の文字列に変換
 * @param date Dateオブジェクト
 * @returns YYYY-MM-DD形式の文字列
 */
export const formatDateForApi = (date: Date): string => {
try {
    return date.toISOString().split('T')[0];
} catch (error) {
    console.error('Date API formatting error:', error);
    return '';
}
};

/**
 * 今日の日付を取得
 * @returns YYYY-MM-DD形式の今日の日付
 */
export const getTodayString = (): string => {
return formatDateForApi(new Date());
};

/**
 * 指定日数後の日付を取得
 * @param daysFromToday 今日からの日数（負の値で過去）
 * @returns YYYY-MM-DD形式の日付文字列
 */
export const getDateString = (daysFromToday: number): string => {
const date = new Date();
date.setDate(date.getDate() + daysFromToday);
return formatDateForApi(date);
};

/**
 * 日付文字列が今日以降かどうかをチェック
 * @param dateString YYYY-MM-DD形式の日付文字列
 * @returns 今日以降の場合true
 */
export const isFutureOrToday = (dateString: string): boolean => {
try {
    const targetDate = new Date(dateString);
    const today = new Date();
    today.setHours(0, 0, 0, 0); // 時刻を00:00:00にリセット
    
    return targetDate >= today;
} catch (error) {
    console.error('Date comparison error:', error);
    return false;
}
};

/**
 * 2つの日付文字列を比較
 * @param date1 YYYY-MM-DD形式の日付文字列
 * @param date2 YYYY-MM-DD形式の日付文字列
 * @returns date1 > date2 の場合 1, date1 < date2 の場合 -1, 同じ場合 0
 */
export const compareDates = (date1: string, date2: string): number => {
try {
    const d1 = new Date(date1);
    const d2 = new Date(date2);
    
    if (d1 > d2) return 1;
    if (d1 < d2) return -1;
    return 0;
} catch (error) {
    console.error('Date comparison error:', error);
    return 0;
}
};