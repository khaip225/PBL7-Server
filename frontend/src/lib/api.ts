const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

function getToken(): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(new RegExp(`(?:^|; )pbl7_auth=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options?.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });
  if (res.status === 401) {
    if (typeof document !== "undefined") {
      document.cookie = "pbl7_auth=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/";
    }
    window.location.href = "/login";
    throw new Error("Unauthorized");
  }
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${await res.text()}`);
  }
  return res.json();
}

// Clients
export const api = {
  clients: {
    list: (params?: Record<string, string>) => {
      const qs = params ? "?" + new URLSearchParams(params).toString() : "";
      return request<any>(`/api/clients${qs}`);
    },
    get: (id: string) => request<any>(`/api/clients/${id}`),
    register: (data: any) => request<any>("/api/clients/register", { method: "POST", body: JSON.stringify(data) }),
    update: (id: string, data: any) => request<any>(`/api/clients/${id}`, { method: "PUT", body: JSON.stringify(data) }),
    heartbeat: (id: string, data: any) => request<any>(`/api/clients/${id}/heartbeat`, { method: "POST", body: JSON.stringify(data) }),
    delete: (id: string) => request<any>(`/api/clients/${id}`, { method: "DELETE" }),
  },
  jobs: {
    list: (params?: Record<string, string>) => {
      const qs = params ? "?" + new URLSearchParams(params).toString() : "";
      return request<any>(`/api/jobs${qs}`);
    },
    get: (id: string) => request<any>(`/api/jobs/${id}`),
    create: (data: any) => request<any>("/api/jobs", { method: "POST", body: JSON.stringify(data) }),
    update: (id: string, data: any) => request<any>(`/api/jobs/${id}`, { method: "PUT", body: JSON.stringify(data) }),
    start: (id: string) => request<any>(`/api/jobs/${id}/start`, { method: "POST" }),
    stop: (id: string) => request<any>(`/api/jobs/${id}/stop`, { method: "POST" }),
    delete: (id: string) => request<any>(`/api/jobs/${id}`, { method: "DELETE" }),
    rounds: (id: string) => request<any>(`/api/jobs/${id}/rounds`),
    progress: (id: string) => request<any>(`/api/jobs/${id}/progress`),
  },
  metrics: {
    overview: () => request<any>("/api/metrics/overview"),
    convergence: (jobId: string) => request<any>(`/api/metrics/job/${jobId}/convergence`),
    communication: (jobId: string) => request<any>(`/api/metrics/job/${jobId}/communication`),
  },
  models: {
    list: (params?: Record<string, string>) => {
      const qs = params ? "?" + new URLSearchParams(params).toString() : "";
      return request<any>(`/api/models${qs}`);
    },
    get: (id: string) => request<any>(`/api/models/${id}`),
    activate: (id: string) => request<any>(`/api/models/${id}/activate`, { method: "POST" }),
    delete: (id: string) => request<any>(`/api/models/${id}`, { method: "DELETE" }),
    downloadUrl: (id: string) => `${BASE_URL}/api/models/${id}/download`,
  },
  events: {
    list: (params?: Record<string, string>) => {
      const qs = params ? "?" + new URLSearchParams(params).toString() : "";
      return request<any>(`/api/events${qs}`);
    },
  },
  settings: {
    list: () => request<any>("/api/settings"),
    get: (key: string) => request<any>(`/api/settings/${key}`),
    update: (key: string, data: any) => request<any>(`/api/settings/${key}`, { method: "PUT", body: JSON.stringify(data) }),
    delete: (key: string) => request<any>(`/api/settings/${key}`, { method: "DELETE" }),
  },
  health: () => request<any>("/api/health"),
  auth: {
    login: (username: string, password: string) =>
      request<any>("/api/auth/login", { method: "POST", body: JSON.stringify({ username, password }) }),
    me: () => request<any>("/api/auth/me"),
  },
};
