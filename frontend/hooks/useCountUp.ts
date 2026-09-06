"use client";

import { useEffect, useState } from "react";

function reducedMotion(): boolean {
  return (
    typeof window !== "undefined" &&
    !!window.matchMedia?.("(prefers-reduced-motion: reduce)").matches
  );
}

/** Eases a number from 0 to `target` once, unless the viewer prefers reduced motion. */
export function useCountUp(target: number, durationMs = 600): number {
  const [value, setValue] = useState(() => (reducedMotion() ? target : 0));

  useEffect(() => {
    if (reducedMotion()) return;
    let raf = 0;
    const start = performance.now();
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / durationMs);
      const eased = 1 - Math.pow(1 - t, 3);
      setValue(Math.round(target * eased));
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, durationMs]);

  return value;
}
