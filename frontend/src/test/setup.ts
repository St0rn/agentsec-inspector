import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";

Object.defineProperty(window, "confirm", { value: () => true, writable: true });

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
