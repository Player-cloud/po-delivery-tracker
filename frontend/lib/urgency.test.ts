import { describe, expect, it } from "vitest";
import { daysRemainingLabel, urgencyOf } from "./urgency";

describe("urgencyOf", () => {
  it("delivered lines are 'delivered' regardless of date", () => {
    expect(urgencyOf({ delivered: true, days_remaining: -20 }).key).toBe("delivered");
    expect(urgencyOf({ delivered: true, days_remaining: 5 }).key).toBe("delivered");
  });

  it("buckets undelivered lines by days remaining", () => {
    expect(urgencyOf({ delivered: false, days_remaining: -1 }).key).toBe("overdue");
    expect(urgencyOf({ delivered: false, days_remaining: 0 }).key).toBe("today");
    expect(urgencyOf({ delivered: false, days_remaining: 1 }).key).toBe("soon");
    expect(urgencyOf({ delivered: false, days_remaining: 7 }).key).toBe("soon");
    expect(urgencyOf({ delivered: false, days_remaining: 8 }).key).toBe("later");
    expect(urgencyOf({ delivered: false, days_remaining: 90 }).key).toBe("later");
  });

  it("matches the backend dashboard partition boundary at 7 days", () => {
    // overdue / today / soon(1..7) / later(>7) — same split as the summary endpoint
    expect(urgencyOf({ delivered: false, days_remaining: 7 }).key).not.toBe("later");
    expect(urgencyOf({ delivered: false, days_remaining: 8 }).key).toBe("later");
  });
});

describe("daysRemainingLabel", () => {
  it("phrases overdue, due-today, and future", () => {
    expect(daysRemainingLabel(-3)).toBe("3d overdue");
    expect(daysRemainingLabel(-1)).toBe("1d overdue");
    expect(daysRemainingLabel(0)).toBe("due today");
    expect(daysRemainingLabel(1)).toBe("1 day");
    expect(daysRemainingLabel(9)).toBe("9 days");
  });
});
