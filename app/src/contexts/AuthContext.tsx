/**
 * Auth0 Authentication Context
 * Manages Auth0 authentication state and provides login/logout functions.
 */
import { createContext, useContext, useState, useEffect, type ReactNode } from "react";
import type { Auth0User } from "@/types/github";

const API_BASE = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || "https://api.yaam.click";

const TOKEN_KEY = "auth0_access_token";
const ID_TOKEN_KEY = "auth0_id_token";
const USER_KEY = "auth0_user";

interface AuthContextType {
  user: Auth0User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (connection?: string) => Promise<void>;
  logout: () => Promise<void>;
  handleCallback: () => Promise<void>;
  getAccessToken: () => string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Auth0User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load user from localStorage on mount
  useEffect(() => {
    const storedUser = localStorage.getItem(USER_KEY);
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch {
        localStorage.removeItem(USER_KEY);
      }
    }
    setIsLoading(false);
  }, []);

  const login = async (connection?: string) => {
    try {
      const redirectUri = `${window.location.origin}/callback`;
      const params = new URLSearchParams({
        redirect_uri: redirectUri,
      });
      if (connection) {
        params.append("connection", connection);
      }

      const response = await fetch(`${API_BASE}/auth0/login?${params.toString()}`);
      const data = await response.json();

      // Redirect to Auth0 login
      window.location.href = data.login_url;
    } catch (error) {
      console.error("Login failed:", error);
      throw error;
    }
  };

  const handleCallback = async () => {
    // Get code and state from URL params
    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");
    const state = params.get("state");

    if (!code) {
      throw new Error("No authorization code in callback");
    }

    try {
      const redirectUri = `${window.location.origin}/callback`;
      const response = await fetch(`${API_BASE}/auth0/callback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code, redirect_uri: redirectUri, state }),
      });

      if (!response.ok) {
        throw new Error("Failed to exchange code for token");
      }

      const data = await response.json();

      // Store tokens
      localStorage.setItem(TOKEN_KEY, data.access_token);
      if (data.id_token) {
        localStorage.setItem(ID_TOKEN_KEY, data.id_token);
      }

      // Store user
      const userData = data.user as Auth0User;
      setUser(userData);
      localStorage.setItem(USER_KEY, JSON.stringify(userData));

      // Clear URL params
      window.history.replaceState({}, "", window.location.pathname);

      // Redirect to home
      window.location.href = "/";
    } catch (error) {
      console.error("Callback handling failed:", error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      // Get logout URL from backend
      const returnTo = `${window.location.origin}`;
      const response = await fetch(`${API_BASE}/auth0/logout?return_to=${encodeURIComponent(returnTo)}`);
      const data = await response.json();

      // Clear local storage
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(ID_TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
      setUser(null);

      // Redirect to Auth0 logout
      window.location.href = data.logout_url;
    } catch (error) {
      console.error("Logout failed:", error);
      // Clear local storage anyway
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(ID_TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
      setUser(null);
    }
  };

  const getAccessToken = () => {
    return localStorage.getItem(TOKEN_KEY);
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    handleCallback,
    getAccessToken,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
