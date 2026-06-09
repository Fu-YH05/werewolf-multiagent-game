import { Play } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';
import ChatBubble from './ChatBubble';

// 硬编码9个玩家数据
const mockPlayers = [
  { id: 1, number: '1号' },
  { id: 2, number: '2号' },
  { id: 3, number: '3号' },
  { id: 4, number: '4号' },
  { id: 5, number: '5号' },
  { id: 6, number: '6号' },
  { id: 7, number: '7号' },
  { id: 8, number: '8号' },
  { id: 9, number: '9号' },
];

// 生成随机星星
const generateStars = () => {
  return Array.from({ length: 50 }, (_, i) => ({
    id: i,
    left: Math.random() * 100,
    top: Math.random() * 100,
    size: Math.random() * 2 + 1,
    delay: Math.random() * 3,
  }));
};

// 示例对话消息
const mockMessage = {
  character: 'Player9',
  action: '（冷静地分析）',
  content: '从昨晚的情况来看，我觉得1号的行为很可疑。他在白天发言时过于急切地想要推动投票，这不符合平民的心态。如果我是预言家，我会查验他的身份。建议大家谨慎投票，不要被情绪左右。',
};

export default function GameScene() {
  const { isNight } = useTheme();
  const stars = generateStars();

  return (
    <div className="relative w-[70%] h-full overflow-hidden">
      {/* 背景 */}
      <div
        className={`absolute inset-0 transition-all duration-1000 ${
          isNight
            ? 'bg-gradient-to-b from-blue-900 to-black'
            : 'bg-gradient-to-b from-sky-300 to-blue-100'
        }`}
      >
        {/* 星星（仅夜晚显示） */}
        {isNight &&
          stars.map((star) => (
            <div
              key={star.id}
              className="star absolute bg-white rounded-full"
              style={{
                left: `${star.left}%`,
                top: `${star.top}%`,
                width: `${star.size}px`,
                height: `${star.size}px`,
                animationDelay: `${star.delay}s`,
              }}
            />
          ))}

        {/* 月亮（仅夜晚显示） */}
        {isNight && (
          <div className="absolute top-10 right-10 w-20 h-20 bg-white rounded-full opacity-80 shadow-lg" />
        )}
      </div>

      {/* 玩家头像列表 */}
      <div className="relative z-10 p-6">
        <div className="flex flex-col space-y-4">
          {mockPlayers.map((player) => (
            <div key={player.id} className="flex items-center space-x-3">
              <div className="w-12 h-12 rounded-full border-2 border-white bg-gray-700 flex items-center justify-center">
                <span className="text-white font-bold">{player.number.charAt(0)}</span>
              </div>
              <span className="text-center text-sm text-white">{player.number}</span>
            </div>
          ))}
        </div>
      </div>

      {/* 对话气泡 */}
      <ChatBubble message={mockMessage} />

      {/* Replay按钮 */}
      <button className="absolute bottom-4 left-1/2 transform -translate-x-1/2 flex items-center space-x-2 px-6 py-3 bg-black hover:bg-gray-800 text-white rounded-full transition-colors">
        <Play className="w-5 h-5 text-yellow-400" />
        <span className="font-medium">REPLAY</span>
      </button>
    </div>
  );
}
