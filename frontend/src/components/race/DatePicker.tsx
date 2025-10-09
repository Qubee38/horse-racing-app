// frontend/src/components/race/DatePicker.tsx (バグ修正版)
import React, { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight, Calendar, Play } from 'lucide-react';

interface DatePickerProps {
  selectedDate: string;
  onDateSelect: (date: string) => void;
  onExecutePrediction?: (date: string) => void;  // 予測実行コールバック追加
  availableDates?: string[];
  minDate?: string;
  maxDate?: string;
  executingPrediction?: boolean;  // 予測実行中フラグ
}

/**
 * バグ修正版日付選択コンポーネント
 * - 日付選択バグの修正
 * - 過去日付の選択許可
 * - 予測実行の統合
 */
const DatePicker: React.FC<DatePickerProps> = ({
  selectedDate,
  onDateSelect,
  onExecutePrediction,
  availableDates = [],
  minDate,
  maxDate,
  executingPrediction = false
}) => {
  // 現在表示している年月
  const [currentYear, setCurrentYear] = useState<number>(new Date().getFullYear());
  const [currentMonth, setCurrentMonth] = useState<number>(new Date().getMonth());
  const [selectedDateObj, setSelectedDateObj] = useState<Date | null>(null);
  const [localSelectedDate, setLocalSelectedDate] = useState<string>('');

  // 選択済み日付を初期化（バグ修正：タイムゾーンを考慮）
  useEffect(() => {
    if (selectedDate) {
      try {
        // YYYY-MM-DD形式の文字列を正しくDateオブジェクトに変換
        const [year, month, day] = selectedDate.split('-').map(Number);
        const date = new Date(year, month - 1, day); // monthは0ベースなので-1
        
        setSelectedDateObj(date);
        setLocalSelectedDate(selectedDate);
        setCurrentYear(date.getFullYear());
        setCurrentMonth(date.getMonth());
      } catch (error) {
        console.warn('Invalid selected date:', selectedDate);
      }
    }
  }, [selectedDate]);

  // 月の情報を取得
  const getDaysInMonth = (year: number, month: number): number => {
    return new Date(year, month + 1, 0).getDate();
  };

  const getFirstDayOfMonth = (year: number, month: number): number => {
    return new Date(year, month, 1).getDay();
  };

  // 年月の変更
  const navigateMonth = (direction: 'prev' | 'next') => {
    if (direction === 'prev') {
      if (currentMonth === 0) {
        setCurrentMonth(11);
        setCurrentYear(currentYear - 1);
      } else {
        setCurrentMonth(currentMonth - 1);
      }
    } else {
      if (currentMonth === 11) {
        setCurrentMonth(0);
        setCurrentYear(currentYear + 1);
      } else {
        setCurrentMonth(currentMonth + 1);
      }
    }
  };

  // 年の直接変更（範囲を拡大）
  const handleYearChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setCurrentYear(parseInt(event.target.value));
  };

  // 月の直接変更
  const handleMonthChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setCurrentMonth(parseInt(event.target.value));
  };

  // 日付クリック処理（バグ修正）
  const handleDateClick = (day: number) => {
    // 正確な日付文字列を生成（タイムゾーン問題を回避）
    const year = currentYear;
    const month = currentMonth + 1; // 0ベースから1ベースに変換
    const dateString = `${year}-${month.toString().padStart(2, '0')}-${day.toString().padStart(2, '0')}`;
    
    // 最小・最大日付チェック（過去日付も許可）
    if (minDate && dateString < minDate && minDate !== '2020-01-01') return; // 過去制限を緩和
    if (maxDate && dateString > maxDate) return;
    
    const clickedDate = new Date(year, currentMonth, day);
    setSelectedDateObj(clickedDate);
    setLocalSelectedDate(dateString);
    
    console.log('Date selected:', dateString); // デバッグ用
    onDateSelect(dateString);
  };

  // 日付が利用可能かチェック（全日付を利用可能とする）
  const isDateAvailable = (day: number): boolean => {
    // 過去日付も含めて全て利用可能とする
    return true;
  };

  // 日付が選択済みかチェック
  const isDateSelected = (day: number): boolean => {
    if (!selectedDateObj) return false;
    
    return (
      selectedDateObj.getFullYear() === currentYear &&
      selectedDateObj.getMonth() === currentMonth &&
      selectedDateObj.getDate() === day
    );
  };

  // 今日の日付かチェック
  const isToday = (day: number): boolean => {
    const today = new Date();
    return (
      today.getFullYear() === currentYear &&
      today.getMonth() === currentMonth &&
      today.getDate() === day
    );
  };

  // 予測実行ボタンの処理
  const handleExecutePrediction = () => {
    if (localSelectedDate && onExecutePrediction) {
      onExecutePrediction(localSelectedDate);
    }
  };

  // カレンダーの日付を生成
  const generateCalendarDays = () => {
    const daysInMonth = getDaysInMonth(currentYear, currentMonth);
    const firstDayOfMonth = getFirstDayOfMonth(currentYear, currentMonth);
    const days = [];

    // 前月の日付を埋める
    const prevMonth = currentMonth === 0 ? 11 : currentMonth - 1;
    const prevYear = currentMonth === 0 ? currentYear - 1 : currentYear;
    const daysInPrevMonth = getDaysInMonth(prevYear, prevMonth);

    for (let i = firstDayOfMonth - 1; i >= 0; i--) {
      days.push({
        day: daysInPrevMonth - i,
        isCurrentMonth: false,
        isPrevMonth: true
      });
    }

    // 当月の日付
    for (let day = 1; day <= daysInMonth; day++) {
      days.push({
        day,
        isCurrentMonth: true,
        isPrevMonth: false
      });
    }

    // 次月の日付を埋める（42日になるまで）
    const remainingDays = 42 - days.length;
    for (let day = 1; day <= remainingDays; day++) {
      days.push({
        day,
        isCurrentMonth: false,
        isPrevMonth: false
      });
    }

    return days;
  };

  const calendarDays = generateCalendarDays();
  const monthNames = [
    '1月', '2月', '3月', '4月', '5月', '6月',
    '7月', '8月', '9月', '10月', '11月', '12月'
  ];

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 w-full max-w-md mx-auto">
      {/* ヘッダー：年月選択 */}
      <div className="flex items-center justify-between mb-6">
        <button
          onClick={() => navigateMonth('prev')}
          className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
          disabled={executingPrediction}
        >
          <ChevronLeft className="w-5 h-5 text-gray-600" />
        </button>

        <div className="flex items-center space-x-2">
          {/* 年選択（範囲拡大：2020年から2030年） */}
          <select
            value={currentYear}
            onChange={handleYearChange}
            disabled={executingPrediction}
            className="text-lg font-semibold border rounded px-2 py-1 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {Array.from({ length: 11 }, (_, i) => {
              const year = 2020 + i;
              return (
                <option key={year} value={year}>
                  {year}年
                </option>
              );
            })}
          </select>

          {/* 月選択 */}
          <select
            value={currentMonth}
            onChange={handleMonthChange}
            disabled={executingPrediction}
            className="text-lg font-semibold border rounded px-2 py-1 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {monthNames.map((month, index) => (
              <option key={index} value={index}>
                {month}
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={() => navigateMonth('next')}
          className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
          disabled={executingPrediction}
        >
          <ChevronRight className="w-5 h-5 text-gray-600" />
        </button>
      </div>

      {/* 曜日ヘッダー */}
      <div className="grid grid-cols-7 mb-2">
        {['日', '月', '火', '水', '木', '金', '土'].map((dayName, index) => (
          <div
            key={dayName}
            className={`text-center text-sm font-medium py-2 ${
              index === 0 ? 'text-red-500' : index === 6 ? 'text-blue-500' : 'text-gray-700'
            }`}
          >
            {dayName}
          </div>
        ))}
      </div>

      {/* カレンダー本体 */}
      <div className="grid grid-cols-7 gap-1">
        {calendarDays.map((dateInfo, index) => {
          const isCurrentMonth = dateInfo.isCurrentMonth;
          const isSelectable = isCurrentMonth && isDateAvailable(dateInfo.day);
          const isSelected = isCurrentMonth && isDateSelected(dateInfo.day);
          const isTodayDate = isCurrentMonth && isToday(dateInfo.day);

          return (
            <button
              key={index}
              onClick={() => isSelectable ? handleDateClick(dateInfo.day) : undefined}
              disabled={!isSelectable || executingPrediction}
              className={`
                h-10 text-sm rounded-lg transition-colors
                ${!isCurrentMonth 
                  ? 'text-gray-300 cursor-default' 
                  : ''
                }
                ${isSelected 
                  ? 'bg-blue-500 text-white font-semibold' 
                  : ''
                }
                ${isTodayDate && !isSelected
                  ? 'bg-blue-100 text-blue-700 font-medium'
                  : ''
                }
                ${isSelectable && !isSelected && !isTodayDate
                  ? 'hover:bg-gray-100 text-gray-700'
                  : ''
                }
                ${!isSelectable && isCurrentMonth
                  ? 'text-gray-400 cursor-not-allowed'
                  : ''
                }
                ${index % 7 === 0 && isCurrentMonth
                  ? 'text-red-600'  // 日曜日
                  : ''
                }
                ${index % 7 === 6 && isCurrentMonth
                  ? 'text-blue-600'  // 土曜日
                  : ''
                }
              `}
            >
              {dateInfo.day}
            </button>
          );
        })}
      </div>

      {/* 選択済み日付表示と予測実行ボタン */}
      <div className="mt-4">
        {localSelectedDate && (
          <div className="text-center mb-4">
            <div className="text-sm text-gray-600 mb-2">
              <Calendar className="w-4 h-4 inline mr-1" />
              選択日: {new Date(localSelectedDate + 'T00:00:00').toLocaleDateString('ja-JP')}
            </div>
            
            {onExecutePrediction && (
              <button
                onClick={handleExecutePrediction}
                disabled={executingPrediction}
                className="bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg font-semibold flex items-center gap-2 mx-auto disabled:cursor-not-allowed transition-colors"
              >
                {executingPrediction ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    予測実行中...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" />
                    この日の予測を実行
                  </>
                )}
              </button>
            )}
          </div>
        )}
        
        <div className="text-xs text-gray-500 text-center space-y-1">
          <div>青色: 今日</div>
          <div>過去の日付も選択可能です</div>
        </div>
      </div>
    </div>
  );
};

export default DatePicker;