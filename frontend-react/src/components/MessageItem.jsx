export default function MessageItem({ message, index }) {
  return (
    <div
      className={`p-4 border-b border-gray-200 ${
        index % 2 === 0 ? 'bg-white' : 'bg-gray-50'
      }`}
    >
      <div className="flex justify-between items-start mb-2">
        <span className="font-medium text-gray-800">
          {message.isSystem ? '系统' : `${message.sender} · ${message.role}`}
        </span>
        <span className="text-xs text-gray-400">{message.timestamp}</span>
      </div>
      <p className="text-gray-700 leading-relaxed">{message.content}</p>
    </div>
  );
}
