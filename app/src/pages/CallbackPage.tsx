/**
 * Auth0 Callback Page
 * Handles the OAuth callback from Auth0
 */
import { useEffect, useState, useRef } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Loader2 } from "lucide-react";

export function CallbackPage() {
  const [error, setError] = useState<string | null>(null);
  const { handleCallback } = useAuth();
  const processingRef = useRef(false);

  useEffect(() => {
    // Prevent multiple concurrent callback processing
    if (processingRef.current) return;
    processingRef.current = true;

    const processCallback = async () => {
      const params = new URLSearchParams(window.location.search);
      const code = params.get("code");
      const errorParam = params.get("error");

      // If Auth0 returned an error, show it and redirect
      if (errorParam) {
        const errorDesc = params.get("error_description") || errorParam;
        setError(errorDesc);
        setTimeout(() => {
          window.location.href = "/";
        }, 3000);
        return;
      }

      // If no code parameter, this might be a direct navigation or something went wrong
      if (!code) {
        setError("No authorization code received. Please try logging in again.");
        setTimeout(() => {
          window.location.href = "/";
        }, 3000);
        return;
      }

      try {
        await handleCallback();
        // handleCallback will redirect to home on success
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

  // Don't render anything until we know we have an error (prevents flash)
  // This ensures a smooth loading experience during redirect
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

  // Always show loading while processing or during redirect
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
