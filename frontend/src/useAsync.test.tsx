import { describe, it, expect } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { useAsync } from "./useAsync";

describe("useAsync", () => {
  it("starts loading, then resolves with data", async () => {
    const { result } = renderHook(() => useAsync(() => Promise.resolve("hello"), []));

    expect(result.current.loading).toBe(true);
    expect(result.current.data).toBeNull();

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.data).toBe("hello");
    expect(result.current.error).toBeNull();
  });

  it("captures errors and stops loading", async () => {
    const boom = new Error("nope");
    const { result } = renderHook(() => useAsync(() => Promise.reject(boom), []));

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.error).toBe(boom);
    expect(result.current.data).toBeNull();
  });
});
