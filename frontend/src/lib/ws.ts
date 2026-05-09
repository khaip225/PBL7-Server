import type { WSMessage } from "./types";

type EventHandler = (msg: WSMessage) => void;

class WSClient {
  private ws: WebSocket | null = null;
  private handlers: Map<string, Set<EventHandler>> = new Map();
  private url: string;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  constructor() {
    this.url = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws";
    if (typeof window !== "undefined") {
      this.connect();
    }
  }

  connect() {
    if (this.ws?.readyState === WebSocket.OPEN) return;
    this.ws = new WebSocket(this.url);
    this.ws.onmessage = (event) => {
      try {
        const msg: WSMessage = JSON.parse(event.data);
        const handlers = this.handlers.get(msg.type);
        if (handlers) handlers.forEach((h) => h(msg));
        const allHandlers = this.handlers.get("*");
        if (allHandlers) allHandlers.forEach((h) => h(msg));
      } catch {}
    };
    this.ws.onclose = () => {
      this.reconnectTimer = setTimeout(() => this.connect(), 3000);
    };
  }

  subscribe(jobId?: string) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ action: "subscribe", job_id: jobId }));
    }
  }

  on(eventType: string, handler: EventHandler) {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, new Set());
    }
    this.handlers.get(eventType)!.add(handler);
    return () => this.handlers.get(eventType)?.delete(handler);
  }

  disconnect() {
    this.reconnectTimer && clearTimeout(this.reconnectTimer);
    this.ws?.close();
  }
}

export const wsClient = typeof window !== "undefined" ? new WSClient() : null;
