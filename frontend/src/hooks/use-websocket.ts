"use client";
import { useEffect, useState } from "react";
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

  return { messages, connected };
}
