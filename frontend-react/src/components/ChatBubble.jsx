export default function ChatBubble({ message }) {
  return (
    <div className="absolute bottom-20 left-1/2 transform -translate-x-1/2 bg-white rounded-lg shadow-lg p-4 max-w-md">
      <div className="font-bold text-gray-800 mb-1">{message.character}</div>
      <div className="italic text-gray-600 text-sm mb-2">{message.action}</div>
      <p className="text-gray-700 leading-relaxed">{message.content}</p>
    </div>
  );
}
