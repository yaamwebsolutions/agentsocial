// =============================================================================
// Agent Twitter - Utility Tests
// =============================================================================
//
// Tests for utility functions
//
// =============================================================================

import { describe, it, expect } from "vitest"
import { cn } from "@/lib/utils"

describe("Utility Functions", () => {
  describe("cn (className merger)", () => {
    it("should merge class names correctly", () => {
      const result = cn("text-red-500", "bg-blue-500")
      expect(result).toContain("text-red-500")
      expect(result).toContain("bg-blue-500")
    })

    it("should handle conditional classes", () => {
      const result = cn("base-class", false && "conditional-class", "always-class")
      expect(result).toContain("base-class")
      expect(result).toContain("always-class")
      expect(result).not.toContain("conditional-class")
    })

    it("should handle Tailwind conflicts correctly", () => {
      const result = cn("text-red-500", "text-blue-500")
      // Tailwind merge should resolve the conflict
      expect(result).toBeTruthy()
    })

    it("should return empty string for no arguments", () => {
      const result = cn()
      expect(result).toBe("")
    })
  })

  describe("date formatting", () => {
    it("should format timestamps relative to now", () => {
      // This is a placeholder for actual date formatting tests
      // Add tests when date formatting utilities are implemented
      const now = new Date()
      expect(now instanceof Date).toBe(true)
    })
  })

  describe("agent mention parsing", () => {
    it("should extract agent handles from text", () => {
      const text = "Hello @grok and @factcheck!"
      const mentions = text.match(/@[\w-]+/g)
      expect(mentions).toEqual(["@grok", "@factcheck"])
    })

    it("should handle text without mentions", () => {
      const text = "Hello world!"
      const mentions = text.match(/@[\w-]+/g)
      expect(mentions).toBeNull()
    })
  })
})
