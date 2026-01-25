/**
 * Auth0 Login Button Component
 * Handles Auth0 Universal Login flow
 */
import { useState } from "react";
import { LogIn } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/AuthContext";

interface Auth0LoginButtonProps {
  className?: string;
  variant?: "default" | "outline" | "ghost" | "secondary";
  size?: "default" | "sm" | "lg";
  fullWidth?: boolean;
  connection?: string; // e.g., "github", "google", or undefined for all
  children?: React.ReactNode;
}

export function Auth0LoginButton({
  className,
  variant = "default",
  size = "default",
  fullWidth = false,
  connection,
  children,
}: Auth0LoginButtonProps) {
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleLogin = async () => {
    setLoading(true);
    try {
      await login(connection);
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
      <LogIn className="w-4 h-4 mr-2" />
      {loading ? "Connecting..." : children || "Log In"}
    </Button>
  );
}
