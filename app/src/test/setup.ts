// =============================================================================
// Agent Twitter - Test Setup
// =============================================================================
//
// Global test configuration for Vitest
//
// =============================================================================

import { expect, afterEach } from "vitest"
import { cleanup } from "@testing-library/react"
import * as matchers from "@testing-library/jest-dom/matchers"

// Extend Vitest's expect with jest-dom matchers
expect.extend(matchers)

// Cleanup after each test
afterEach(() => {
  cleanup()
})

// Mock window.matchMedia
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => {},
  }),
})

// Mock IntersectionObserver
class IntersectionObserver {
  observe() {}
  disconnect() {}
  unobserve() {}
}

Object.defineProperty(window, "IntersectionObserver", {
  writable: true,
  configurable: true,
  value: IntersectionObserver,
})

// Mock ResizeObserver
class ResizeObserver {
  observe() {}
  disconnect() {}
  unobserve() {}
}

Object.defineProperty(window, "ResizeObserver", {
  writable: true,
  configurable: true,
  value: ResizeObserver,
})
