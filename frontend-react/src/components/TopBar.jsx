import { Moon, Sun, Play, Square, Download, Zap, Dog } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

export default function TopBar() {
  const { isNight, toggleTheme } = useTheme();

  return (
    <nav className="bg-gray-900 h-16 flex items-center justify-between px-6">
      {/* 左侧：品牌标识 */}
      <div className="flex items-center space-x-2">
        <Dog className="w-8 h-8 text-white" />
        <span className="text-xl font-bold text-white">WolfWind</span>
      </div>

      {/* 中间：功能按钮组 */}
      <div className="flex items-center space-x-4">
        {/* 夜晚/白天切换按钮 */}
        <button
          onClick={toggleTheme}
          className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-white transition-colors"
        >
          {isNight ? (
            <>
              <Moon className="w-5 h-5" />
              <span>夜晚模式</span>
            </>
          ) : (
            <>
              <Sun className="w-5 h-5" />
              <span>白天模式</span>
            </>
          )}
        </button>

        {/* 已连接状态标签 */}
        <div className="flex items-center space-x-2 px-3 py-2 bg-green-900/30 rounded-full">
          <span className="w-2 h-2 bg-green-500 rounded-full"></span>
          <span className="text-green-400 text-sm">已连接</span>
        </div>

        {/* 功能按钮 */}
        <button className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white transition-colors">
          <Play className="w-5 h-5" />
          <span>开始游戏</span>
        </button>

        <button className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white transition-colors">
          <Square className="w-5 h-5" />
          <span>终止游戏</span>
        </button>

        <button className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-gray-700 hover:bg-gray-600 text-white transition-colors">
          <Download className="w-5 h-5" />
          <span>导出日志</span>
        </button>

        <button className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-gray-700 hover:bg-gray-600 text-white transition-colors">
          <Zap className="w-5 h-5" />
          <span>导出经验</span>
        </button>
      </div>
    </nav>
  );
}
