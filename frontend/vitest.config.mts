import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    // Pure-logic unit tests only for now (lib/). Component tests would add a
    // jsdom + testing-library setup — a follow-up if we want them.
    include: ["lib/**/*.test.ts"],
    environment: "node",
  },
});
