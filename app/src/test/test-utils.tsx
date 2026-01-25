// =============================================================================
// Agent Twitter - Test Utilities
// =============================================================================
//
// Helper functions for testing React components
//
// =============================================================================

import { render, RenderOptions } from "@testing-library/react"
import { ReactElement } from "react"

// Custom render function that includes providers
interface CustomRenderOptions extends Omit<RenderOptions, "wrapper"> {
  // Add custom options here if needed
}

export function renderWithProviders(
  ui: ReactElement,
  options?: CustomRenderOptions
) {
  // TODO: Wrap with actual providers (Router, Theme, etc.)
  // For now, just use the default render
  return render(ui, options)
}

// Re-export everything from testing-library
export * from "@testing-library/react"
export { default as userEvent } from "@testing-library/user-event"
