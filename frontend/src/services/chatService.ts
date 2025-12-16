import { Message, SuggestionResponse } from '../types/chat';
import { DiagramStructure } from '../contexts/DiagramContext';

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const chatService = {
  async sendMessage(history: Message[], diagram: DiagramStructure, signal?: AbortSignal): Promise<ReadableStream<Uint8Array> | null> {
    const response = await fetch(`${API_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ history, diagram }),
      signal,
    });

    if (!response.ok) {
      throw new Error(`Network error: ${response.statusText}`);
    }

    return response.body;
  },

  async getSuggestions(history: Message[], diagram: DiagramStructure): Promise<string[]> {
    const response = await fetch(`${API_URL}/suggest-followups`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ history, diagram }),
    });

    if (!response.ok) {
      throw new Error('Failed to fetch suggestions');
    }

    const data: SuggestionResponse = await response.json();
    return data.suggestions || [];
  },

  async wakeUpServer(): Promise<void> {
    try {
      await fetch(`${API_URL}/ping`, { method: "GET" });
    } catch (err) {
      console.warn("Server wake-up failed:", err);
    }
  }
}; 