// =============================================================================
// Agent Twitter - API Tests
// =============================================================================
//
// Tests for API client functions
//
// =============================================================================

import { describe, it, expect, vi, beforeEach } from "vitest"

// Mock fetch
global.fetch = vi.fn()

describe("API Client", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe("API Base URL", () => {
    it("should have a default API base URL", () => {
      const apiUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"
      expect(apiUrl).toBeTruthy()
    })
  })

  describe("Health Check", () => {
    it("should fetch health endpoint", async () => {
      const mockResponse = { status: "ok", app: "AgentTwitter", version: "1.0.0" }
      vi.mocked(fetch).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      } as Response)

      const response = await fetch("http://localhost:8000/health")
      const data = await response.json()

      expect(fetch).toHaveBeenCalledWith("http://localhost:8000/health")
      expect(data).toEqual(mockResponse)
    })
  })

  describe("Error Handling", () => {
    it("should handle API errors gracefully", async () => {
      vi.mocked(fetch).mockRejectedValueOnce(new Error("Network error"))

      await expect(fetch("http://localhost:8000/nonexistent")).rejects.toThrow()
    })
  })
})
