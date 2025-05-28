const TypingIndicator = () => {
  return (
    <div className="flex justify-start">
      <div className="bg-gray-200 text-gray-800 rounded-2xl rounded-bl-none px-4 py-2 shadow-sm">
        <div className="flex space-x-1">
          <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
          <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
          <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
        </div>
      </div>
    </div>
  )
}

export default TypingIndicator