import MessageItem from './MessageItem';

// 硬编码消息数据
const mockMessages = [
  {
    id: 1,
    sender: '系统',
    role: '',
    isSystem: true,
    timestamp: '22:01:35',
    content: '游戏开始！天黑请闭眼，狼人请行动。',
  },
  {
    id: 2,
    sender: '9号',
    role: 'werewolf',
    isSystem: false,
    timestamp: '22:02:18',
    content: '昨晚我查验了1号，他是狼人！今天必须先出他。',
  },
  {
    id: 3,
    sender: '系统',
    role: '',
    isSystem: true,
    timestamp: '22:03:42',
    content: '天亮了！昨晚平安夜，没有人被淘汰。',
  },
  {
    id: 4,
    sender: '5号',
    role: 'villager',
    isSystem: false,
    timestamp: '22:04:55',
    content: '我是平民，昨晚没有任何信息。建议大家都说说自己的想法。',
  },
  {
    id: 5,
    sender: '9号',
    role: 'werewolf',
    isSystem: false,
    timestamp: '22:06:30',
    content: '从昨晚的情况来看，我觉得1号的行为很可疑。他在白天发言时过于急切地想要推动投票，这不符合平民的心态。如果我是预言家，我会查验他的身份。建议大家谨慎投票，不要被情绪左右。',
  },
];

export default function GameLog() {
  return (
    <div className="w-[30%] h-full flex flex-col bg-gray-50">
      {/* 标题栏 */}
      <div className="bg-gray-100 px-4 py-3 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-gray-800">游戏记录</h2>
          <span className="text-sm text-gray-500">{mockMessages.length}条</span>
        </div>
      </div>

      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto">
        {mockMessages.map((message, index) => (
          <MessageItem key={message.id} message={message} index={index} />
        ))}
      </div>
    </div>
  );
}
