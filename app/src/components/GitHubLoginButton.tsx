/**
 * GitHub Login Button Component
 * Handles GitHub OAuth login flow
 */

import { useState } from "react";
import { Github } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";

const API_BASE = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || "http://localhost:8000";

interface GitHubLoginButtonProps {
  className?: string;
  variant?: "default" | "outline" | "ghost" | "secondary";
  size?: "default" | "sm" | "lg";
  fullWidth?: boolean;
}

export function GitHubLoginButton({
  className,
  variant = "default",
  size = "default",
  fullWidth = false,
}: GitHubLoginButtonProps) {
  const [loading, setLoading] = useState(false);
  const navigate = navigate();

  const handleLogin = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/auth/github/login`);
      const data = await response.json();

      // Redirect to GitHub OAuth page
      window.location.href = data.auth_url;
    } catch (error) {
      console.error("Login failed:", error);
      setLoading(false);
    }
  };

  return (
    <Button
      onClick={handleLogin}
      disabled={loading}
      variant={variant}
      size={size}
      className={className}
      {...(fullWidth && { className: "w-full" })}
    >
      <Github className="w-4 h-4 mr-2" />
      {loading ? "Connecting..." : "Continue with GitHub"}
    </Button>
  );
}
