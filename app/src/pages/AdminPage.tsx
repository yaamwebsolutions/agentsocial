import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Shield, CheckCircle, Copy, ArrowLeft } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { useState } from "react";
import { toast } from "sonner";

const API_BASE = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || "https://api.yaam.click";

interface UserInfo {
  authenticated?: boolean;
  user_id?: string;
  email?: string;
  name?: string;
  sub?: string;
  iss?: string;
  error?: string;
  [key: string]: string | boolean | undefined;
}

export function AdminPage() {
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();
  const [userInfo, setUserInfo] = useState<UserInfo | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchUserInfo = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("auth0_access_token");
      const response = await fetch(`${API_BASE}/admin/whoami`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        setUserInfo(data);
      } else {
        const error = await response.json();
        setUserInfo({ error: error.detail || "Failed to fetch user info" });
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Network error";
      setUserInfo({ error: errorMessage });
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    toast.success(`Copied ${label}`);
  };

  if (!isAuthenticated) {
    return (
      <div className="max-w-2xl mx-auto py-12 px-4">
        <Card className="border-0 rounded-2xl bg-muted/30 p-8 text-center">
          <Shield className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
          <h2 className="text-xl font-bold mb-2">Authentication Required</h2>
          <p className="text-muted-foreground mb-4">Please log in to access admin features.</p>
          <Button onClick={() => navigate("/")}>Back to Home</Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto py-6 px-4">
      {/* Header */}
      <div className="flex items-center gap-4 mb-6">
        <Button variant="ghost" size="sm" onClick={() => navigate(-1)} className="rounded-full">
          <ArrowLeft className="w-5 h-5" />
        </Button>
        <div className="flex items-center gap-2">
          <Shield className="w-6 h-6 text-primary" />
          <h1 className="text-2xl font-bold">Admin Configuration</h1>
        </div>
      </div>

      {/* User Info from AuthContext */}
      <Card className="border-0 rounded-2xl bg-muted/30 p-6 mb-4">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <CheckCircle className="w-5 h-5 text-green-500" />
          Logged In User
        </h2>
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 rounded-lg bg-background">
            <span className="text-sm text-muted-foreground">Name</span>
            <span className="font-medium">{user?.name || "N/A"}</span>
          </div>
          <div className="flex items-center justify-between p-3 rounded-lg bg-background">
            <span className="text-sm text-muted-foreground">Email</span>
            <span className="font-medium">{user?.email || "N/A"}</span>
          </div>
          <div className="flex items-center justify-between p-3 rounded-lg bg-background">
            <span className="text-sm text-muted-foreground">User ID (sub)</span>
            <code className="text-xs bg-muted px-2 py-1 rounded max-w-[200px] truncate">
              {user?.sub || "N/A"}
            </code>
          </div>
        </div>
      </Card>

      {/* Fetch Full User Info */}
      {!userInfo && (
        <Card className="border-0 rounded-2xl bg-muted/30 p-6 mb-4">
          <h2 className="text-lg font-semibold mb-4">Get Admin Info</h2>
          <p className="text-sm text-muted-foreground mb-4">
            Click below to fetch detailed user information including your user ID for admin configuration.
          </p>
          <Button onClick={fetchUserInfo} disabled={loading} className="w-full">
            {loading ? "Loading..." : "Fetch User Info"}
          </Button>
        </Card>
      )}

      {/* Detailed User Info */}
      {userInfo && (
        <Card className="border-0 rounded-2xl bg-muted/30 p-6 mb-4">
          <h2 className="text-lg font-semibold mb-4">Detailed User Info</h2>
          {userInfo.error ? (
            <div className="p-4 rounded-lg bg-destructive/10 text-destructive">
              {userInfo.error}
            </div>
          ) : (
            <div className="space-y-3">
              {Object.entries(userInfo)
                .filter(([key, value]) =>
                  !["instructions", "example"].includes(key) &&
                  value !== null &&
                  typeof value !== "object"
                )
                .map(([key, value]) => (
                  <div key={key} className="flex items-center justify-between p-3 rounded-lg bg-background group">
                    <span className="text-sm text-muted-foreground capitalize">{key.replace(/_/g, " ")}</span>
                    <div className="flex items-center gap-2">
                      <code className="text-xs bg-muted px-2 py-1 rounded max-w-[200px] truncate">
                        {String(value)}
                      </code>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="opacity-0 group-hover:opacity-100 transition-opacity"
                        onClick={() => copyToClipboard(String(value), key)}
                      >
                        <Copy className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                ))}
            </div>
          )}
        </Card>
      )}

      {/* Instructions */}
      <Card className="border-0 rounded-2xl bg-primary/5 p-6">
        <h2 className="text-lg font-semibold mb-4">Configure Admin Access</h2>
        <ol className="list-decimal list-inside space-y-2 text-sm">
          <li>Copy your <code className="bg-muted px-1 rounded">user_id</code> or <code className="bg-muted px-1 rounded">sub</code> from above</li>
          <li>Go to Render Dashboard: <a href="https://dashboard.render.com/web/srv-d5qg6onpm1nc738qeg30/env-vars" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">Environment Variables</a></li>
          <li>Add or update <code className="bg-muted px-1 rounded">ADMIN_USER_IDS</code> with your user ID</li>
          <li>Set <code className="bg-muted px-1 rounded">ADMIN_EMAIL_DOMAINS</code> to empty if you want only yourself as admin</li>
          <li>Save and the service will restart automatically</li>
        </ol>
      </Card>
    </div>
  );
}
