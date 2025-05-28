import { useEffect, useRef } from 'react'

const ChatBubble = ({ message, isLatest }) => {
  const bubbleRef = useRef(null)

  useEffect(() => {
    if (isLatest && bubbleRef.current) {
      bubbleRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [isLatest])

  const getBubbleStyle = () => {
    if (message.role === 'user') {
      return 'bg-indigo-600 text-white rounded-br-none'
    } else if (message.role === 'assistant') {
      return 'bg-gray-200 text-gray-800 rounded-bl-none'
    } else if (message.isError) {
      return 'bg-red-100 text-red-800 border border-red-200'
    } else {
      return 'bg-yellow-100 text-yellow-800 border border-yellow-200'
    }
  }

  const getAlignment = () => {
    return message.role === 'user' ? 'justify-end' : 'justify-start'
  }

  return (
    <div className={`flex ${getAlignment()}`} ref={bubbleRef}>
      <div className={`max-w-[80%] p-4 rounded-2xl ${getBubbleStyle()} shadow-sm`}>
        <div className="whitespace-pre-wrap break-words">
          {message.content}
        </div>
        {message.escalated && (
          <div className="mt-2 text-xs text-indigo-700">
            <span className="font-semibold">Note:</span> Your case has been escalated
          </div>
        )}
      </div>
    </div>
  )
}

export default ChatBubble