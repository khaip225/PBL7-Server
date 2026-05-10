"use client";
import { useEffect, useState, useCallback } from "react";
import { wsClient } from "@/lib/ws";
import type { WSMessage } from "@/lib/types";

export function useWebSocket(jobId?: string) {
  const [messages, setMessages] = useState<WSMessage[]>([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (!wsClient) return;

    wsClient.subscribe(jobId);
    setConnected(true);

    const unsub = wsClient.on("*", (msg: WSMessage) => {
      if (!jobId || msg.payload?.job_id === jobId || !msg.payload?.job_id) {
        setMessages((prev) => [...prev.slice(-200), msg]);
      }
    });

    return () => {
      unsub();
    };
  }, [jobId]);

  const clear = useCallback(() => setMessages([]), []);

  return { messages, connected, clear };
}

export function useWSEvent(eventType: string, jobId?: string) {
  const [lastEvent, setLastEvent] = useState<WSMessage | null>(null);

  useEffect(() => {
    if (!wsClient) return;
    wsClient.subscribe(jobId);
    const unsub = wsClient.on(eventType, (msg) => setLastEvent(msg));
    return () => { unsub(); };
  }, [eventType, jobId]);

  return lastEvent;
}
