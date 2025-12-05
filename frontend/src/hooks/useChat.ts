import { useState, useCallback, useRef, useEffect } from 'react';
import { Message } from '../types/chat';
import { chatService } from '../services/chatService';

const CHAT_HISTORY_KEY = "chat_history";

export const useChat = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const activeRequestsRef = useRef<Set<AbortController>>(new Set());

  const handleMessagesLoad = useCallback((loadedMessages: Message[]) => {
    setMessages(loadedMessages);
  }, []);

  const clearChat = useCallback(() => {
    // Abort all active requests
    activeRequestsRef.current.forEach(controller => controller.abort());
    activeRequestsRef.current.clear();

    setMessages([]);
    setSuggestions([]);
    setIsSending(false);
    setIsTyping(false);
    localStorage.removeItem(CHAT_HISTORY_KEY);
  }, []);

  const sendMessage = useCallback(async (messageToSend: string) => {
    // Only check if message is empty, allow concurrent requests
    if (!messageToSend.trim()) return;

    const userMessage: Message = { content: messageToSend, role: "user" };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInput("");
    setSuggestions([]);

    // Create a new controller for this request
    const controller = new AbortController();
    activeRequestsRef.current.add(controller);

    // Track the message index for this specific request
    const assistantMessageIndex = newMessages.length;

    try {
      const stream = await chatService.sendMessage(newMessages, controller.signal);
      if (!stream) return;

      // Add assistant message placeholder at the correct index
      setMessages((prev) => {
        const updated = [...prev];
        updated.splice(assistantMessageIndex, 0, { content: "", role: "assistant" });
        return updated;
      });

      const reader = stream.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunkValue = decoder.decode(value, { stream: true });
        setMessages((prev) => {
          const updated = [...prev];
          // Update the assistant message at the specific index
          if (updated[assistantMessageIndex]) {
            updated[assistantMessageIndex] = {
              ...updated[assistantMessageIndex],
              content: updated[assistantMessageIndex].content + chunkValue,
            };
          }
          return updated;
        });
      }

      // Get suggestions after this specific conversation completes
      const currentMessages = [...newMessages];
      setMessages((prev) => {
        if (prev[assistantMessageIndex]) {
          currentMessages.push(prev[assistantMessageIndex]);
        }
        return prev;
      });

      const suggestions = await chatService.getSuggestions(currentMessages);
      setSuggestions(suggestions);
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") {
        console.log("Request was aborted");
      } else {
        const errorMessage: Message = {
          content: "Error fetching response: " + (error instanceof Error ? error.message : "Unknown error"),
          role: "assistant",
        };
        setMessages((prev) => {
          const updated = [...prev];
          updated.splice(assistantMessageIndex, 0, errorMessage);
          return updated;
        });
      }
    } finally {
      // Remove this controller from active requests
      activeRequestsRef.current.delete(controller);
    }
  }, [messages]);

  useEffect(() => {
    chatService.wakeUpServer();
  }, []);

  return {
    messages,
    input,
    setInput,
    isSending,
    isTyping,
    suggestions,
    clearChat,
    sendMessage,
    onMessagesLoad: handleMessagesLoad,
  };
}; 