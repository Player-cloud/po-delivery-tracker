"use client";

import { useSyncExternalStore } from "react";
import { getServerToken, getToken, getUserRole, subscribe } from "./auth";

export type Auth = {
  token: string | null;
  loggedIn: boolean;
  role: string | null;
  isAdmin: boolean;
};

/** Subscribe to the auth token. Re-renders on login, logout, and cross-tab change. */
export function useAuth(): Auth {
  const token = useSyncExternalStore(subscribe, getToken, getServerToken);
  const role = token ? getUserRole() : null;
  return { token, loggedIn: token !== null, role, isAdmin: role === "administrator" };
}
