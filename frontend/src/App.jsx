import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import { v4 as uuidv4 } from 'uuid'
import ChatBubble from './components/ChatBubble'
import ChatInput from './components/ChatInput'
import TypingIndicator from './components/TypingIndicator'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function App() {
  const [messages, setMessages] = useState([])
  const [sessionId] = useState(uuidv4())
  const [isTyping, setIsTyping] = useState(false)
  const [sessionEnded, setSessionEnded] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async (message) => {
    if (!message.trim() || sessionEnded) return

    // Add user message
    const userMessage = { role: 'user', content: message }
    setMessages(prev => [...prev, userMessage])
    setIsTyping(true)

    try {
      const response = await axios.post(`${API_URL}/chat/`, {
        session_id: sessionId,
        message: message
      })

      const botMessage = { 
        role: 'assistant', 
        content: response.data.response,
        escalated: response.data.escalated,
        sessionEnd: response.data.session_end
      }

      setMessages(prev => [...prev, botMessage])
      
      if (response.data.escalated) {
        const escalationMessage = {
          role: 'system',
          content: 'Your case has been escalated to a human agent',
          isSystem: true
        }
        setMessages(prev => [...prev, escalationMessage])
      }

      if (response.data.session_end) {
        setSessionEnded(true)
      }
    } catch (error) {
      const errorMessage = {
        role: 'system',
        content: 'Connection error. Please try again.',
        isError: true
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsTyping(false)
    }
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-indigo-600 text-white p-4 shadow-md">
        <div className="container mx-auto flex items-center">
          <img src="/logo.svg" alt="Logo" className="h-8 mr-3" />
          <h1 className="text-xl font-bold">Agentic Support</h1>
          <div className="ml-auto text-sm">
            Session: {sessionId.slice(0, 8)}
          </div>
        </div>
      </header>

      {/* Chat Container */}
      <div className="flex-1 overflow-y-auto p-4 container mx-auto max-w-4xl">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <div className="text-center p-6 max-w-md">
              <h2 className="text-2xl font-bold mb-2">Welcome to Agentic Support</h2>
              <p className="mb-4">How can I help you today?</p>
              <div className="grid grid-cols-2 gap-2">
                <button 
                  onClick={() => sendMessage("I need technical help")}
                  className="bg-indigo-100 hover:bg-indigo-200 text-indigo-800 py-2 px-4 rounded-lg transition"
                >
                  Technical Help
                </button>
                <button 
                  onClick={() => sendMessage("I have a feature request")}
                  className="bg-green-100 hover:bg-green-200 text-green-800 py-2 px-4 rounded-lg transition"
                >
                  Feature Request
                </button>
                <button 
                  onClick={() => sendMessage("I'm interested in your product")}
                  className="bg-purple-100 hover:bg-purple-200 text-purple-800 py-2 px-4 rounded-lg transition"
                >
                  Sales Inquiry
                </button>
                <button 
                  onClick={() => sendMessage("Other question")}
                  className="bg-gray-100 hover:bg-gray-200 text-gray-800 py-2 px-4 rounded-lg transition"
                >
                  Other Question
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((message, index) => (
              <ChatBubble 
                key={index}
                message={message}
                isLatest={index === messages.length - 1}
              />
            ))}
            {isTyping && <TypingIndicator />}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 bg-white p-4">
        <div className="container mx-auto max-w-4xl">
          <ChatInput 
            onSend={sendMessage} 
            disabled={sessionEnded}
            placeholder={sessionEnded ? "This session has ended. Refresh to start a new chat." : "Type your message..."}
          />
        </div>
      </div>
    </div>
  )
}

export default App