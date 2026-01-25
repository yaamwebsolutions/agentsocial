import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowLeft, User, Palette, Bell, Shield, Github, Star, Share2, Trash2, Download, Moon, Sun, Monitor, Link2, Heart } from "lucide-react";
import { useCurrentUser } from "@/hooks/useApi";
import { useTheme } from "@/contexts/ThemeContext";
import { useAuth } from "@/contexts/AuthContext";
import { toast } from "sonner";

interface SettingSectionProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  children: React.ReactNode;
}

function SettingSection({ icon, title, description, children }: SettingSectionProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-primary/10 text-primary">
          {icon}
        </div>
        <div>
          <h3 className="font-semibold text-foreground">{title}</h3>
          <p className="text-sm text-muted-foreground">{description}</p>
        </div>
      </div>
      <div className="ml-13">
        {children}
      </div>
    </div>
  );
}

interface ToggleProps {
  enabled: boolean;
  onChange: (enabled: boolean) => void;
  label: string;
  description?: string;
}

function Toggle({ enabled, onChange, label, description }: ToggleProps) {
  return (
    <div className="flex items-center justify-between py-3 border-b border-border/50 last:border-0">
      <div className="flex-1">
        <div className="font-medium text-foreground">{label}</div>
        {description && <div className="text-sm text-muted-foreground">{description}</div>}
      </div>
      <button
        type="button"
        onClick={() => onChange(!enabled)}
        aria-pressed={enabled ? "true" : "false"}
        aria-label={`Toggle ${label.toLowerCase()}`}
        className={`relative w-14 h-7 rounded-full transition-all duration-300 flex-shrink-0 ${
          enabled ? "bg-primary" : "bg-muted"
        }`}
      >
        <div
          className={`absolute top-1 w-5 h-5 rounded-full bg-white shadow-md transition-all duration-300 ${
            enabled ? "left-8" : "left-1"
          }`}
        />
      </button>
    </div>
  );
}

export function SettingsPage() {
  const navigate = useNavigate();
  const { theme, setTheme } = useTheme();
  const { user, logout } = useAuth();
  const { user: currentUser } = useCurrentUser();

  // Settings state
  const [notifications, setNotifications] = useState({
    mentions: true,
    replies: true,
    agentResponses: true,
    weeklyDigest: false,
  });
  const [privacy, setPrivacy] = useState({
    profileVisible: true,
    showActivity: true,
    allowDirectMessages: true,
  });

  // GitHub stats
  const [githubStars, setGithubStars] = useState(0);
  const [hasStarred, setHasStarred] = useState(false);

  useEffect(() => {
    // Fetch GitHub stars
    fetch("https://api.github.com/repos/yaamwebsolutions/agentsocial")
      .then((res) => res.json())
      .then((data) => {
        setGithubStars(data.stargazers_count || 0);
      })
      .catch(() => {});

    // Check if user has starred (if they have GitHub connected)
    if (user?.github_login) {
      // In a real app, you'd check the GitHub API
    }
  }, [user]);

  const handleStarRepo = () => {
    window.open("https://github.com/yaamwebsolutions/agentsocial", "_blank");
    setHasStarred(true);
    toast.success("Thank you for starring! ⭐");
  };

  const handleShareRepo = async () => {
    const shareUrl = "https://github.com/yaamwebsolutions/agentsocial";
    const shareText = "Check out AgentSocial - An AI-native social platform where you can @mention AI agents! 🤖";

    if (navigator.share) {
      try {
        await navigator.share({
          title: "AgentSocial - AI-Native Social Platform",
          text: shareText,
          url: shareUrl,
        });
        toast.success("Thanks for sharing!");
      } catch (e) {
        // User canceled or error
      }
    } else {
      // Fallback: copy to clipboard
      navigator.clipboard.writeText(`${shareText} ${shareUrl}`);
      toast.success("Link copied to clipboard!");
    }
  };

  const handleCopyEmbed = () => {
    const embedCode = `<a href="https://github.com/yaamwebsolutions/agentsocial" target="_blank">
  <img alt="AgentSocial" src="https://img.shields.io/badge/AgentSocial-AI%20Native%20Social-FF6B00?logo=github" />
</a>`;
    navigator.clipboard.writeText(embedCode);
    toast.success("Embed code copied!");
  };

  const handleSignOut = () => {
    logout();
    navigate("/");
  };

  const handleSetTheme = (value: string) => {
    if (value === "system") {
      const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      setTheme(prefersDark ? "dark" : "light");
    } else {
      setTheme(value as "light" | "dark");
    }
  };

  const handleClearData = () => {
    if (confirm("Are you sure you want to clear all local data? This will log you out.")) {
      localStorage.clear();
      window.location.href = "/";
    }
  };

  const themeOptions = [
    { value: "light", icon: Sun, label: "Light" },
    { value: "dark", icon: Moon, label: "Dark" },
    { value: "system", icon: Monitor, label: "System" },
  ] as const;

  const isDark = theme === "dark";

  return (
    <div className="max-w-3xl mx-auto py-6 px-4 pb-20">
      {/* Header */}
      <div className="flex items-center gap-4 mb-8">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate(-1)}
          className="rounded-full"
        >
          <ArrowLeft className="w-5 h-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold">Settings</h1>
          <p className="text-muted-foreground">Customize your experience</p>
        </div>
      </div>

      {/* GitHub Promotion Card */}
      <Card className={`border-0 rounded-2xl overflow-hidden mb-6 ${
        isDark
          ? "bg-gradient-to-br from-amber-500/10 via-yellow-500/10 to-orange-500/10"
          : "bg-gradient-to-br from-amber-50 via-yellow-50 to-orange-50"
      }`}>
        <div className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                isDark
                  ? "bg-gradient-to-br from-amber-400 to-yellow-600"
                  : "bg-gradient-to-br from-gray-800 to-gray-900"
              }`}>
                <Github className="w-6 h-6 text-white" />
              </div>
              <div>
                <h2 className="font-bold text-lg">Star us on GitHub!</h2>
                <p className="text-sm text-muted-foreground">
                  Help us grow. {githubStars.toLocaleString()} stars already!
                </p>
              </div>
            </div>
            <Button
              onClick={handleStarRepo}
              className={`rounded-full gap-2 ${
                isDark
                  ? "bg-white text-black hover:bg-gray-100"
                  : "bg-black text-white hover:bg-gray-800"
              }`}
            >
              <Star className={`w-4 h-4 ${hasStarred ? "fill-current" : ""}`} />
              {hasStarred ? "Starred!" : "Star"}
            </Button>
          </div>

          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleShareRepo}
              className="rounded-full gap-2"
            >
              <Share2 className="w-4 h-4" />
              Share Project
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleCopyEmbed}
              className="rounded-full gap-2"
            >
              <Link2 className="w-4 h-4" />
              Copy Badge
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => window.open("https://github.com/yaamwebsolutions/agentsocial", "_blank")}
              className="rounded-full gap-2"
            >
              <Github className="w-4 h-4" />
              View Code
            </Button>
          </div>
        </div>

        {/* Animated GitHub banner */}
        <div className={`h-1 w-full ${
          isDark
            ? "bg-gradient-to-r from-amber-500 via-yellow-500 to-orange-500"
            : "bg-gradient-to-r from-gray-900 via-gray-700 to-gray-900"
        }`} />
      </Card>

      {/* Profile Card */}
      <Card className="border-0 rounded-2xl overflow-hidden mb-6 bg-card">
        <div className="p-6">
          <SettingSection
            icon={<User className="w-5 h-5" />}
            title="Profile Information"
            description="Manage your account details"
          >
            <div className="bg-muted/30 rounded-xl p-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Display Name</span>
                <span className="font-medium">{currentUser?.display_name || user?.name || "User"}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Username</span>
                <span className="font-medium">@{currentUser?.handle || user?.nickname || "user"}</span>
              </div>
              {user?.email && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Email</span>
                  <span className="font-medium text-sm">{user.email}</span>
                </div>
              )}
              {user?.github_login && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">GitHub</span>
                  <span className="font-medium flex items-center gap-1">
                    <Github className="w-4 h-4" /> @{user.github_login}
                  </span>
                </div>
              )}
            </div>
          </SettingSection>
        </div>
      </Card>

      {/* Appearance Card */}
      <Card className="border-0 rounded-2xl overflow-hidden mb-6 bg-card">
        <div className="p-6">
          <SettingSection
            icon={<Palette className="w-5 h-5" />}
            title="Appearance"
            description="Customize how the app looks"
          >
            <div className="bg-muted/30 rounded-xl p-4">
              <div className="text-sm text-muted-foreground mb-3">Theme</div>
              <div className="grid grid-cols-3 gap-2">
                {themeOptions.map(({ value, icon: Icon, label }) => (
                  <button
                    key={value}
                    onClick={() => handleSetTheme(value)}
                    className={`flex flex-col items-center gap-2 p-4 rounded-xl transition-all ${
                      theme === value
                        ? "bg-primary text-primary-foreground scale-105 shadow-lg"
                        : "bg-background hover:bg-muted"
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    <span className="text-sm font-medium">{label}</span>
                    {theme === value && (
                      <div className="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-card" />
                    )}
                  </button>
                ))}
              </div>
            </div>
          </SettingSection>
        </div>
      </Card>

      {/* Notifications Card */}
      <Card className="border-0 rounded-2xl overflow-hidden mb-6 bg-card">
        <div className="p-6">
          <SettingSection
            icon={<Bell className="w-5 h-5" />}
            title="Notifications"
            description="Choose what notifications you receive"
          >
            <div className="bg-muted/30 rounded-xl">
              <Toggle
                enabled={notifications.mentions}
                onChange={(v) => setNotifications({ ...notifications, mentions: v })}
                label="Mentions"
                description="Get notified when someone mentions you"
              />
              <Toggle
                enabled={notifications.replies}
                onChange={(v) => setNotifications({ ...notifications, replies: v })}
                label="Replies"
                description="Get notified when someone replies to your posts"
              />
              <Toggle
                enabled={notifications.agentResponses}
                onChange={(v) => setNotifications({ ...notifications, agentResponses: v })}
                label="Agent Responses"
                description="Get notified when an AI agent responds"
              />
              <Toggle
                enabled={notifications.weeklyDigest}
                onChange={(v) => setNotifications({ ...notifications, weeklyDigest: v })}
                label="Weekly Digest"
                description="Receive a weekly summary of activity"
              />
            </div>
          </SettingSection>
        </div>
      </Card>

      {/* Privacy Card */}
      <Card className="border-0 rounded-2xl overflow-hidden mb-6 bg-card">
        <div className="p-6">
          <SettingSection
            icon={<Shield className="w-5 h-5" />}
            title="Privacy"
            description="Control your privacy settings"
          >
            <div className="bg-muted/30 rounded-xl">
              <Toggle
                enabled={privacy.profileVisible}
                onChange={(v) => setPrivacy({ ...privacy, profileVisible: v })}
                label="Public Profile"
                description="Allow others to see your profile"
              />
              <Toggle
                enabled={privacy.showActivity}
                onChange={(v) => setPrivacy({ ...privacy, showActivity: v })}
                label="Activity Status"
                description="Show when you're active"
              />
              <Toggle
                enabled={privacy.allowDirectMessages}
                onChange={(v) => setPrivacy({ ...privacy, allowDirectMessages: v })}
                label="Direct Messages"
                description="Allow others to message you directly"
              />
            </div>
          </SettingSection>
        </div>
      </Card>

      {/* Data & Danger Zone */}
      <Card className="border-0 rounded-2xl overflow-hidden mb-6 bg-card">
        <div className="p-6">
          <SettingSection
            icon={<Trash2 className="w-5 h-5 text-destructive" />}
            title="Data Management"
            description="Manage your local data"
          >
            <div className="bg-muted/30 rounded-xl p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium">Export Your Data</div>
                  <div className="text-sm text-muted-foreground">Download a copy of your data</div>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    const data = { user, posts: [], settings: { notifications, privacy } };
                    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement("a");
                    a.href = url;
                    a.download = `agentsocial-data-${new Date().toISOString().split("T")[0]}.json`;
                    a.click();
                    toast.success("Data exported successfully!");
                  }}
                  className="rounded-full gap-2"
                >
                  <Download className="w-4 h-4" />
                  Export
                </Button>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium text-destructive">Clear Local Data</div>
                  <div className="text-sm text-muted-foreground">Delete all locally stored data</div>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleClearData}
                  className="rounded-full gap-2 text-destructive hover:text-destructive"
                >
                  <Trash2 className="w-4 h-4" />
                  Clear
                </Button>
              </div>
            </div>
          </SettingSection>
        </div>
      </Card>

      {/* Sign Out */}
      <Button
        variant="outline"
        onClick={handleSignOut}
        className="w-full rounded-full h-12 font-medium border-destructive/30 text-destructive hover:bg-destructive/10"
      >
        Sign Out
      </Button>

      {/* Footer with GitHub love */}
      <div className="mt-8 text-center">
        <p className="text-sm text-muted-foreground mb-2">
          Built with <Heart className="w-4 h-4 inline text-red-500" /> by{" "}
          <a
            href="https://yaam.click"
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary hover:underline"
          >
            Yaam Web Solutions
          </a>
        </p>
        <a
          href="https://github.com/yaamwebsolutions/agentsocial"
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs text-muted-foreground hover:text-primary flex items-center justify-center gap-1"
        >
          <Github className="w-3 h-3" />
          Open Source on GitHub
        </a>
      </div>
    </div>
  );
}
