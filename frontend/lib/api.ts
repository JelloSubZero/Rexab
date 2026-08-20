import type {
  AuthResponse,
  Dashboard,
  Member,
  Payment,
  Room,
  Settlement,
  User,
} from "@/types/api";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  code: string;
  status: number;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

export function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  return "Something went wrong. Please try again.";
}

let authToken: string | null = null;

export function setAuthToken(token: string | null) {
  authToken = token;
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");

  if (authToken) {
    headers.set("Authorization", `Bearer ${authToken}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 204) {
    return undefined as T;
  }

  const body = await response.json().catch(() => null);

  if (!response.ok) {
    const code = body?.error?.code ?? "UNKNOWN_ERROR";
    const message =
      body?.error?.message ?? "Something went wrong. Please try again.";
    throw new ApiError(response.status, code, message);
  }

  return body as T;
}

export const api = {
  auth: {
    register: (data: { email: string; password: string; first_name: string }) =>
      request<AuthResponse>("/api/auth/register", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    login: (data: { email: string; password: string }) =>
      request<AuthResponse>("/api/auth/login", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    me: () => request<User>("/api/auth/me"),
    logout: () => request<void>("/api/auth/logout", { method: "POST" }),
  },
  rooms: {
    list: () => request<Room[]>("/api/rooms"),
    create: (name: string) =>
      request<Room>("/api/rooms", {
        method: "POST",
        body: JSON.stringify({ name }),
      }),
    join: (code: string) =>
      request<Room>("/api/rooms/join", {
        method: "POST",
        body: JSON.stringify({ code }),
      }),
    get: (roomId: number) => request<Room>(`/api/rooms/${roomId}`),
    delete: (roomId: number) =>
      request<void>(`/api/rooms/${roomId}`, { method: "DELETE" }),
    leave: (roomId: number) =>
      request<void>(`/api/rooms/${roomId}/leave`, { method: "POST" }),
    dashboard: (roomId: number) =>
      request<Dashboard>(`/api/rooms/${roomId}/dashboard`),
  },
  members: {
    list: (roomId: number) =>
      request<Member[]>(`/api/rooms/${roomId}/members`),
    remove: (roomId: number, userId: number) =>
      request<void>(`/api/rooms/${roomId}/members/${userId}`, {
        method: "DELETE",
      }),
  },
  payments: {
    list: (roomId: number) =>
      request<Payment[]>(`/api/rooms/${roomId}/payments`),
    create: (
      roomId: number,
      data: { user_id: number; amount: number; description?: string },
    ) =>
      request<Payment>(`/api/rooms/${roomId}/payments`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
  },
  settlements: {
    list: (roomId: number) =>
      request<Settlement[]>(`/api/rooms/${roomId}/settlements`),
    create: (
      roomId: number,
      data: { from_user_id: number; to_user_id: number; amount: number },
    ) =>
      request<Settlement>(`/api/rooms/${roomId}/settlements`, {
        method: "POST",
        body: JSON.stringify(data),
      }),
    confirm: (settlementId: number) =>
      request<Settlement>(`/api/settlements/${settlementId}/confirm`, {
        method: "POST",
      }),
  },
};
