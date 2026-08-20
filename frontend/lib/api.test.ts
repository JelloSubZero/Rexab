import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api, ApiError, getErrorMessage, setAuthToken } from "@/lib/api";

function mockFetchOnce(response: {
  status: number;
  body?: unknown;
}) {
  global.fetch = vi.fn().mockResolvedValue({
    status: response.status,
    ok: response.status >= 200 && response.status < 300,
    json: async () => response.body,
  }) as unknown as typeof fetch;
}

describe("api client", () => {
  beforeEach(() => {
    setAuthToken(null);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("attaches the bearer token once set", async () => {
    setAuthToken("test-token");
    mockFetchOnce({ status: 200, body: [] });

    await api.rooms.list();

    const [, options] = (fetch as ReturnType<typeof vi.fn>).mock.calls[0];
    const headers = options.headers as Headers;

    expect(headers.get("Authorization")).toBe("Bearer test-token");
  });

  it("omits the Authorization header when no token is set", async () => {
    mockFetchOnce({ status: 200, body: [] });

    await api.rooms.list();

    const [, options] = (fetch as ReturnType<typeof vi.fn>).mock.calls[0];
    const headers = options.headers as Headers;

    expect(headers.has("Authorization")).toBe(false);
  });

  it("throws an ApiError built from the {error:{code,message}} body", async () => {
    mockFetchOnce({
      status: 403,
      body: { error: { code: "NOT_ROOM_MEMBER", message: "Nope." } },
    });

    await expect(api.rooms.get(1)).rejects.toMatchObject({
      status: 403,
      code: "NOT_ROOM_MEMBER",
      message: "Nope.",
    });
  });

  it("falls back to a generic error when the body isn't the expected shape", async () => {
    mockFetchOnce({ status: 500, body: null });

    await expect(api.rooms.get(1)).rejects.toMatchObject({
      code: "UNKNOWN_ERROR",
    });
  });

  it("returns undefined for 204 No Content responses", async () => {
    mockFetchOnce({ status: 204 });

    await expect(api.rooms.leave(1)).resolves.toBeUndefined();
  });
});

describe("getErrorMessage", () => {
  it("returns the ApiError's message", () => {
    const error = new ApiError(409, "CONFLICT", "Something conflicted.");
    expect(getErrorMessage(error)).toBe("Something conflicted.");
  });

  it("returns a generic message for non-ApiError values", () => {
    expect(getErrorMessage(new Error("boom"))).toBe(
      "Something went wrong. Please try again.",
    );
    expect(getErrorMessage("boom")).toBe(
      "Something went wrong. Please try again.",
    );
  });
});
