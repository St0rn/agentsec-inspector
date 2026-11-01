import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterEach, beforeEach, vi } from "vitest";

Object.defineProperty(window, "confirm", { value: () => true, writable: true });

beforeEach(() => localStorage.setItem("agentsec-language", "fr"));

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
