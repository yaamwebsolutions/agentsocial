/**
 * Auth0 Callback Page
 * Handles the OAuth callback from Auth0
 */
import { useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Loader2 } from "lucide-react";

export function CallbackPage() {
  const [error, setError] = useState<string | null>(null);
  const { handleCallback } = useAuth();

  useEffect(() => {
    const processCallback = async () => {
      // Wait for URL params to be available (fixes race condition on redirect)
      const params = new URLSearchParams(window.location.search);
      const code = params.get("code");
      const errorParam = params.get("error");

      // If no params yet, wait a bit and retry (handles browser navigation timing)
      if (!code && !errorParam) {
        const timeoutId = setTimeout(() => {
          processCallback();
        }, 100);
        return () => clearTimeout(timeoutId);
      }

      // If Auth0 returned an error, show it and redirect
      if (errorParam) {
        const errorDesc = params.get("error_description") || errorParam;
        setError(errorDesc);
        setTimeout(() => {
          window.location.href = "/";
        }, 3000);
        return;
      }

      try {
        await handleCallback();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Authentication failed");
        // Redirect to home after error
        setTimeout(() => {
          window.location.href = "/";
        }, 3000);
      }
    };

    processCallback();
  }, [handleCallback]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center space-y-4">
          <div className="text-destructive text-6xl">⚠️</div>
          <h1 className="text-2xl font-bold">Authentication Failed</h1>
          <p className="text-muted-foreground">{error}</p>
          <p className="text-sm text-muted-foreground">Redirecting to home...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="text-center space-y-4">
        <Loader2 className="w-12 h-12 animate-spin mx-auto text-primary" />
        <h1 className="text-xl font-semibold">Completing sign in...</h1>
        <p className="text-muted-foreground">Please wait while we verify your account.</p>
      </div>
    </div>
  );
}
