import { afterEach, describe, expect, it, vi } from "vitest";
import { getToken, getUserRole } from "./auth";

/** Build a JWT-shaped string with the given payload (signature is irrelevant here). */
function fakeJwt(payload: Record<string, unknown>): string {
  const b64 = (o: unknown) => Buffer.from(JSON.stringify(o)).toString("base64");
  return `${b64({ alg: "HS256", typ: "JWT" })}.${b64(payload)}.sig`;
}

const store = new Map<string, string>();
vi.stubGlobal("localStorage", {
  getItem: (k: string) => store.get(k) ?? null,
  setItem: (k: string, v: string) => void store.set(k, v),
  removeItem: (k: string) => void store.delete(k),
});
vi.stubGlobal("window", {});

afterEach(() => store.clear());

describe("getUserRole", () => {
  it("returns null when there is no token", () => {
    expect(getToken()).toBeNull();
    expect(getUserRole()).toBeNull();
  });

  it("extracts the role claim from the token", () => {
    store.set("access_token", fakeJwt({ sub: "1", role: "administrator" }));
    expect(getUserRole()).toBe("administrator");
  });

  it("returns null for a malformed token", () => {
    store.set("access_token", "not-a-jwt");
    expect(getUserRole()).toBeNull();
  });

  it("returns null when the token has no role claim", () => {
    store.set("access_token", fakeJwt({ sub: "1" }));
    expect(getUserRole()).toBeNull();
  });
});
