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

export const api = {
  clients: {
    list: (params?: Record<string, string>) => {
      const qs = params ? "?" + new URLSearchParams(params).toString() : "";
      return request<any>(`/api/clients${qs}`);
    },
  },
  jobs: {
    list: (params?: Record<string, string>) => {
      const qs = params ? "?" + new URLSearchParams(params).toString() : "";
      return request<any>(`/api/jobs${qs}`);
    },
    create: (data: any) => request<any>("/api/jobs", { method: "POST", body: JSON.stringify(data) }),
    start: (id: string) => request<any>(`/api/jobs/${id}/start`, { method: "POST" }),
    stop: (id: string) => request<any>(`/api/jobs/${id}/stop`, { method: "POST" }),
  },
  metrics: {
    overview: () => request<any>("/api/metrics/overview"),
    convergence: (jobId: string) => request<any>(`/api/metrics/job/${jobId}/convergence`),
    prototypeEvolution: (jobId: string) => request<any>(`/api/metrics/job/${jobId}/prototype-evolution`),
  },
  models: {
    list: (params?: Record<string, string>) => {
      const qs = params ? "?" + new URLSearchParams(params).toString() : "";
      return request<any>(`/api/models${qs}`);
    },
    activate: (id: string) => request<any>(`/api/models/${id}/activate`, { method: "POST" }),
    delete: (id: string) => request<any>(`/api/models/${id}`, { method: "DELETE" }),
    downloadUrl: (id: string) => `${BASE_URL}/api/models/${id}/download`,
  },
  settings: {
    list: () => request<any>("/api/settings"),
    update: (key: string, data: any) => request<any>(`/api/settings/${key}`, { method: "PUT", body: JSON.stringify(data) }),
    reset: () => request<any>("/api/settings/reset", { method: "POST" }),
  },
  health: () => request<any>("/api/health"),
};
