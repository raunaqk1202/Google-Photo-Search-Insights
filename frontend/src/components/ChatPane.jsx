import React, { useRef, useEffect } from 'react';
import { Sparkle, Trash2, MoreVertical, Sparkles, ArrowUp } from 'lucide-react';

const ChatPane = ({
  messages,
  setMessages,
  inputValue,
  setInputValue,
  isTyping,
  handleSendMessage,
  renderFormattedText
}) => {
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  return (
    <aside className="w-full flex-1 flex flex-col h-full bg-white relative">
      
      {/* Chat Header */}
      <div className="h-14 px-5 border-b border-[#dadce0] flex items-center justify-between bg-white shrink-0">
        <div className="flex items-center space-x-2.5">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-blue-500 via-indigo-500 to-purple-500 flex items-center justify-center text-white shadow-xs">
            <Sparkle className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-gray-900 flex items-center gap-1.5">
              UX Research Assistant
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
            </h2>

          </div>
        </div>

        <div className="flex items-center gap-1">
          <button 
            onClick={() => setMessages([])}
            className="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
            title="Clear Chat"
          >
            <Trash2 className="w-4 h-4" />
          </button>
          <button className="p-1.5 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors">
            <MoreVertical className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Chat Thread Messages */}
      <div className="flex-1 overflow-y-auto p-4 md:p-5 space-y-4 bg-gradient-to-b from-white to-[#F8FAFD]/60">
        

        {messages.map((msg) => {
          const isUser = msg.sender === 'user';
          if (!isUser && !msg.text) return null;
          return (
            <div 
              key={msg.id} 
              className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}
            >
              <div className="flex items-center gap-1.5 mb-1 px-1">
                {!isUser && (
                  <div className="w-4 h-4 rounded-full bg-gradient-to-r from-blue-600 to-purple-600 flex items-center justify-center">
                    <Sparkles className="w-2.5 h-2.5 text-white" />
                  </div>
                )}
                <span className="text-[11px] font-semibold text-gray-500">
                  {isUser ? 'You (Product Lead)' : 'UX Assistant'}
                </span>
                <span className="text-[10px] text-gray-400">{msg.timestamp}</span>
              </div>

              <div
                className={`max-w-[90%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                  isUser
                    ? 'bg-[#e8f0fe] text-blue-950 font-medium rounded-tr-none shadow-xs border border-blue-100'
                    : 'bg-white text-gray-800 rounded-tl-none shadow-elevation-1 border border-gray-200/80'
                }`}
              >
                <div className="whitespace-pre-wrap break-words">
                  {isUser ? msg.text : renderFormattedText(msg.text)}
                </div>
              </div>
            </div>
          );
        })}

        {isTyping && (
          <div className="flex items-start flex-col">
            <div className="flex items-center gap-1.5 mb-1 px-1">
              <div className="w-4 h-4 rounded-full bg-google-blue flex items-center justify-center">
                <Sparkles className="w-2.5 h-2.5 text-white" />
              </div>
              <span className="text-[11px] font-semibold text-gray-500">UX Assistant is evaluating evidence...</span>
            </div>
            <div className="bg-white rounded-2xl rounded-tl-none px-4 py-3 shadow-elevation-1 border border-gray-200 flex items-center space-x-1.5">
              <span className="w-2 h-2 rounded-full bg-google-blue animate-bounce"></span>
              <span className="w-2 h-2 rounded-full bg-google-red animate-bounce [animation-delay:0.15s]"></span>
              <span className="w-2 h-2 rounded-full bg-google-yellow animate-bounce [animation-delay:0.3s]"></span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>



      {/* Input Bar */}
      <div className="p-4 bg-white border-t border-[#dadce0] shrink-0">
        <form 
          onSubmit={handleSendMessage}
          className="relative flex items-center bg-[#F1F3F4] hover:bg-[#E8EAED] focus-within:bg-white focus-within:ring-2 focus-within:ring-google-blue/30 focus-within:border-google-blue rounded-full border border-transparent transition-all shadow-sm pl-4 pr-1.5 py-1.5"
        >
          <Sparkles className="w-4 h-4 text-google-blue mr-2 shrink-0" />
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Ask UX Research about user friction..."
            className="w-full bg-transparent border-none text-sm text-gray-800 placeholder-gray-500 focus:outline-none focus:ring-0 py-1"
          />
          <button
            type="submit"
            disabled={!inputValue.trim() || isTyping}
            className={`w-9 h-9 rounded-full flex items-center justify-center transition-all ${
              inputValue.trim() && !isTyping
                ? 'bg-google-blue text-white hover:bg-google-blueHover shadow-xs cursor-pointer'
                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
            }`}
          >
            <ArrowUp className="w-4 h-4" />
          </button>
        </form>

      </div>
    </aside>
  );
};

export default ChatPane;
