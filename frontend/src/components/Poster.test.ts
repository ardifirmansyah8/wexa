import { describe, it, expect } from "vitest";
import { initials, posterStyle } from "./Poster";

describe("initials", () => {
  it("takes the first letter of the first two words, uppercased", () => {
    expect(initials("The Dark Knight")).toBe("TD");
    expect(initials("Inception")).toBe("I");
  });

  it("ignores punctuation", () => {
    expect(initials("Spider-Man: Homecoming")).toBe("SH");
  });
});

describe("posterStyle", () => {
  it("is deterministic for the same title", () => {
    expect(posterStyle("Inception")).toEqual(posterStyle("Inception"));
  });

  it("produces a linear-gradient background", () => {
    expect(posterStyle("Dune").background).toMatch(/^linear-gradient\(/);
  });
});
