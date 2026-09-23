/**
 * useChat — custom hook for chat state management and SSE streaming.
 * Full implementation in Phase 5.
 */

import { useState } from "react";

export default function useChat() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);

  const sendMessage = async (query) => {
    // Stub — Phase 5 will implement SSE streaming
    console.log("Chat query (stub):", query);
  };

  const clearChat = () => {
    setMessages([]);
    setSessionId(null);
  };

  return { messages, isLoading, sessionId, sendMessage, clearChat };
}
