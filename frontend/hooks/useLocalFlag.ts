"use client";

import { useCallback, useSyncExternalStore } from "react";

const EVENT = "po-tracker:localflag";

function emit() {
  window.dispatchEvent(new Event(EVENT));
}

/** A boolean persisted in localStorage ("1" / absent), reactive within the tab
 *  and across tabs. Returns [value, setTrue]. */
export function useLocalFlag(key: string): [boolean, () => void] {
  const subscribe = useCallback((cb: () => void) => {
    const onStorage = (e: StorageEvent) => {
      if (e.key === key) cb();
    };
    window.addEventListener(EVENT, cb);
    window.addEventListener("storage", onStorage);
    return () => {
      window.removeEventListener(EVENT, cb);
      window.removeEventListener("storage", onStorage);
    };
  }, [key]);

  const value = useSyncExternalStore(
    subscribe,
    () => {
      try {
        return localStorage.getItem(key) === "1";
      } catch {
        return false;
      }
    },
    () => false,
  );

  const setTrue = useCallback(() => {
    try {
      localStorage.setItem(key, "1");
    } catch {
      /* ignore */
    }
    emit();
  }, [key]);

  return [value, setTrue];
}
