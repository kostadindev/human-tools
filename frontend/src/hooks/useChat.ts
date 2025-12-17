import { useState, useCallback, useRef, useEffect } from 'react';
import { Message } from '../types/chat';
import { chatService } from '../services/chatService';
import { useDiagram } from '../contexts/DiagramContext';

const CHAT_HISTORY_KEY = "chat_history";

export const useChat = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const activeRequestsRef = useRef<Set<AbortController>>(new Set());
  const { diagramStructure } = useDiagram();

  const handleMessagesLoad = useCallback((loadedMessages: Message[]) => {
    setMessages(loadedMessages);
  }, []);

  const clearChat = useCallback(() => {
    // Abort all active requests
    activeRequestsRef.current.forEach(controller => controller.abort());
    activeRequestsRef.current.clear();

    setMessages([]);
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

    // Create a new controller for this request
    const controller = new AbortController();
    activeRequestsRef.current.add(controller);

    // Track the message index for this specific request
    const assistantMessageIndex = newMessages.length;

    try {
      const stream = await chatService.sendMessage(newMessages, diagramStructure, controller.signal);
      if (!stream) return;

      // Add assistant message placeholder at the correct index
      setMessages((prev) => {
        const updated = [...prev];
        updated.splice(assistantMessageIndex, 0, { content: "", role: "assistant" });
        return updated;
      });

      // Set typing indicator to true when starting to receive response
      setIsTyping(true);

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

      // Set typing indicator to false when response is complete
      setIsTyping(false);
    } catch (error) {
      // Set typing indicator to false on error
      setIsTyping(false);

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
  }, [messages, diagramStructure]);

  useEffect(() => {
    chatService.wakeUpServer();
  }, []);

  return {
    messages,
    input,
    setInput,
    isSending,
    isTyping,
    clearChat,
    sendMessage,
    onMessagesLoad: handleMessagesLoad,
  };
}; 