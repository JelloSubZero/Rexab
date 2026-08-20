import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AuthProvider, useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";

vi.mock("@/lib/api", () => ({
  api: {
    auth: {
      login: vi.fn(),
      register: vi.fn(),
      me: vi.fn(),
      logout: vi.fn(),
    },
  },
  setAuthToken: vi.fn(),
}));

const mockUser = {
  id: 1,
  email: "daniel@example.com",
  username: null,
  first_name: "Daniel",
  telegram_id: null,
};

function TestConsumer() {
  const { user, isLoading, login, logout } = useAuth();

  if (isLoading) return <p>loading</p>;

  return (
    <div>
      <p>{user ? `signed in as ${user.first_name}` : "signed out"}</p>
      <button onClick={() => login("daniel@example.com", "password123")}>
        log in
      </button>
      <button onClick={logout}>log out</button>
    </div>
  );
}

describe("AuthProvider", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.mocked(api.auth.me).mockReset();
    vi.mocked(api.auth.login).mockReset();
    vi.mocked(api.auth.logout).mockReset().mockResolvedValue(undefined);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("starts signed out with no stored token", async () => {
    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    await waitFor(() =>
      expect(screen.getByText("signed out")).toBeInTheDocument(),
    );
  });

  it("restores the session from a stored token via /me", async () => {
    localStorage.setItem("rexab_token", "stored-token");
    vi.mocked(api.auth.me).mockResolvedValue(mockUser);

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    await waitFor(() =>
      expect(
        screen.getByText("signed in as Daniel"),
      ).toBeInTheDocument(),
    );
  });

  it("clears an invalid stored token instead of getting stuck", async () => {
    localStorage.setItem("rexab_token", "expired-token");
    vi.mocked(api.auth.me).mockRejectedValue(new Error("401"));

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    await waitFor(() =>
      expect(screen.getByText("signed out")).toBeInTheDocument(),
    );
    expect(localStorage.getItem("rexab_token")).toBeNull();
  });

  it("login stores the token and updates the user", async () => {
    vi.mocked(api.auth.me).mockResolvedValue(mockUser);
    vi.mocked(api.auth.login).mockResolvedValue({
      access_token: "fresh-token",
      token_type: "bearer",
      user: mockUser,
    });

    const user = userEvent.setup();

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    await waitFor(() =>
      expect(screen.getByText("signed out")).toBeInTheDocument(),
    );

    await user.click(screen.getByText("log in"));

    await waitFor(() =>
      expect(
        screen.getByText("signed in as Daniel"),
      ).toBeInTheDocument(),
    );
    expect(localStorage.getItem("rexab_token")).toBe("fresh-token");
  });

  it("logout clears the token and user even if the API call fails", async () => {
    localStorage.setItem("rexab_token", "stored-token");
    vi.mocked(api.auth.me).mockResolvedValue(mockUser);
    vi.mocked(api.auth.logout).mockRejectedValue(new Error("network"));

    const user = userEvent.setup();

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>,
    );

    await waitFor(() =>
      expect(
        screen.getByText("signed in as Daniel"),
      ).toBeInTheDocument(),
    );

    await act(async () => {
      await user.click(screen.getByText("log out"));
    });

    expect(screen.getByText("signed out")).toBeInTheDocument();
    expect(localStorage.getItem("rexab_token")).toBeNull();
  });
});
