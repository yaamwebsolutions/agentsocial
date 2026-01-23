// =============================================================================
// Agent Twitter - Type Definition Tests
// =============================================================================
//
// Tests for TypeScript type definitions
//
// =============================================================================

import { describe, it, expect } from "vitest"
import type { Agent, Post, Thread, User } from "@/types/api"

describe("API Types", () => {
  describe("Agent Type", () => {
    it("should accept valid agent data", () => {
      const agent: Agent = {
        id: "test-agent",
        handle: "@test",
        name: "Test Agent",
        role: "Testing",
        policy: "Test policy",
        style: "Test style",
        tools: ["test"],
        color: "#FF0000",
        icon: "🧪",
      }
      expect(agent.id).toBe("test-agent")
      expect(agent.handle).toBe("@test")
    })

    it("should accept optional mock responses", () => {
      const agent: Agent = {
        id: "test-agent",
        handle: "@test",
        name: "Test Agent",
        role: "Testing",
        policy: "Test policy",
        style: "Test style",
        tools: [],
        color: "#FF0000",
        icon: "🧪",
        mock_responses: ["Response 1", "Response 2"],
      }
      expect(agent.mock_responses).toHaveLength(2)
    })
  })

  describe("Post Type", () => {
    it("should accept valid post data", () => {
      const user: User = {
        id: "user-1",
        username: "testuser",
        display_name: "Test User",
        handle: "@testuser",
        avatar_url: "",
        bio: "",
      }

      const post: Post = {
        id: "post-1",
        text: "Hello world!",
        author: user,
        timestamp: "2024-01-01T12:00:00Z",
      }
      expect(post.id).toBe("post-1")
      expect(post.text).toBe("Hello world!")
    })

    it("should accept optional parent_id", () => {
      const user: User = {
        id: "user-1",
        username: "testuser",
        display_name: "Test User",
        handle: "@testuser",
        avatar_url: "",
        bio: "",
      }

      const post: Post = {
        id: "post-1",
        text: "Reply!",
        author: user,
        timestamp: "2024-01-01T12:00:00Z",
        parent_id: "post-0",
      }
      expect(post.parent_id).toBe("post-0")
    })
  })

  describe("User Type", () => {
    it("should accept valid user data", () => {
      const user: User = {
        id: "user-1",
        username: "testuser",
        display_name: "Test User",
        handle: "@testuser",
        avatar_url: "https://example.com/avatar.jpg",
        bio: "Test bio",
      }
      expect(user.id).toBe("user-1")
      expect(user.username).toBe("testuser")
    })
  })

  describe("Thread Type", () => {
    it("should accept valid thread data", () => {
      const user: User = {
        id: "user-1",
        username: "testuser",
        display_name: "Test User",
        handle: "@testuser",
        avatar_url: "",
        bio: "",
      }

      const post: Post = {
        id: "post-1",
        text: "Hello world!",
        author: user,
        timestamp: "2024-01-01T12:00:00Z",
      }

      const thread: Thread = {
        id: "thread-1",
        root_post: post,
        replies: [],
      }
      expect(thread.id).toBe("thread-1")
      expect(thread.root_post).toEqual(post)
      expect(thread.replies).toHaveLength(0)
    })
  })
})
