import { useState } from "react";
import { Bot, Home, Users, Settings, MoreVertical, LogOut, User as UserIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useNavigate, useLocation } from "react-router-dom";
import { CommandPalette } from "./CommandPalette";
import { ThemeSwitcher } from "./ThemeSwitcher";
import { NotificationsDropdown } from "./NotificationsDropdown";
import { SettingsModal } from "./SettingsModal";
import { Auth0LoginButton } from "./Auth0LoginButton";
import { useAgents } from "@/hooks/useApi";
import { useTheme } from "@/contexts/ThemeContext";
import { useAuth } from "@/contexts/AuthContext";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

export function Header() {
  const navigate = useNavigate();
  const location = useLocation();
  const { agents } = useAgents();
  const { theme } = useTheme();
  const { user, isAuthenticated, logout, isLoading } = useAuth();
  const [settingsOpen, setSettingsOpen] = useState(false);

  const handleCreatePost = (text: string) => {
    const composer = document.getElementById("composer-textarea") as HTMLTextAreaElement;
    if (composer) {
      composer.value = text;
      composer.focus();
      composer.dispatchEvent(new Event("input", { bubbles: true }));
    }
  };

  const handleSearch = (query: string) => {
    navigate(`/?search=${encodeURIComponent(query)}`);
  };

  const isDark = theme === "dark";

  return (
    <>
      <header className="sticky top-0 z-50 bg-background/80 backdrop-blur-xl border-b border-border/50">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex items-center justify-between h-14">
            {/* Logo */}
            <div
              className="flex items-center gap-3 cursor-pointer group"
              onClick={() => navigate("/")}
            >
              <div className={`w-9 h-9 rounded-xl flex items-center justify-center shadow-sm transition-all duration-300 ${
                isDark
                  ? "bg-gradient-to-br from-amber-400 via-yellow-500 to-amber-600 shadow-amber-500/20"
                  : "bg-gradient-to-br from-amber-500 via-yellow-500 to-amber-600 shadow-amber-500/30"
              } group-hover:scale-105 group-hover:shadow-md`}>
                <Bot className="w-5 h-5 text-white" />
              </div>
              <span className={`font-semibold text-lg hidden sm:block bg-gradient-to-r bg-clip-text text-transparent ${
                isDark
                  ? "from-amber-300 via-yellow-400 to-amber-400"
                  : "from-amber-600 via-yellow-600 to-amber-700"
              }`}>
                AgentTwitter
              </span>
            </div>

            {/* Center - Search / Command Palette */}
            <div className="hidden md:flex flex-1 max-w-md mx-6">
              <CommandPalette
                agents={agents || []}
                onCreatePost={handleCreatePost}
                onSearch={handleSearch}
              />
            </div>

            {/* Nav */}
            <nav className="flex items-center gap-1">
              <Button
                variant={location.pathname === "/" ? "secondary" : "ghost"}
                size="sm"
                onClick={() => navigate("/")}
                className="rounded-full h-8 px-3 text-xs font-medium"
              >
                <Home className="w-3.5 h-3.5" />
                <span className="hidden sm:inline ml-1.5">Home</span>
              </Button>
              <Button
                variant={location.pathname === "/agents" ? "secondary" : "ghost"}
                size="sm"
                onClick={() => navigate("/agents")}
                className="rounded-full h-8 px-3 text-xs font-medium"
              >
                <Users className="w-3.5 h-3.5" />
                <span className="hidden sm:inline ml-1.5">Agents</span>
              </Button>

              {/* Theme Switcher */}
              <div className="hidden md:block">
                <ThemeSwitcher />
              </div>

              {/* Auth Section - Desktop */}
              <div className="hidden md:flex items-center gap-1 ml-1">
                <NotificationsDropdown />
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSettingsOpen(true)}
                  className="rounded-full h-8 w-8 p-0"
                >
                  <Settings className="w-3.5 h-3.5" />
                </Button>

                {/* User / Login */}
                {!isLoading && isAuthenticated && user ? (
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="sm" className="rounded-full h-8 w-8 p-0">
                        <Avatar className="h-8 w-8">
                          <AvatarImage src={user.picture} alt={user.name || "User"} />
                          <AvatarFallback>
                            <UserIcon className="h-3.5 w-3.5" />
                          </AvatarFallback>
                        </Avatar>
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-48">
                      <div className="px-2 py-1.5 text-sm font-medium">
                        {user.name || user.nickname}
                      </div>
                      <div className="px-2 py-1 text-xs text-muted-foreground">
                        {user.email}
                      </div>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem onClick={() => logout()}>
                        <LogOut className="w-4 h-4 mr-2" />
                        Sign out
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                ) : !isLoading ? (
                  <Auth0LoginButton size="sm" variant="default">
                    Sign In
                  </Auth0LoginButton>
                ) : null}
              </div>

              {/* Mobile Menu */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="sm" className="rounded-full h-8 w-8 p-0 md:hidden">
                    <MoreVertical className="w-4 h-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-44">
                  <DropdownMenuItem onClick={() => navigate("/")}>
                    <Home className="w-4 h-4 mr-2" />
                    Home
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => navigate("/agents")}>
                    <Users className="w-4 h-4 mr-2" />
                    Agents
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={() => setSettingsOpen(true)}>
                    <Settings className="w-4 h-4 mr-2" />
                    Settings
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  {isAuthenticated && user ? (
                    <>
                      <div className="px-2 py-1.5 text-xs font-medium">
                        {user.name || user.nickname}
                      </div>
                      <DropdownMenuItem onClick={() => logout()}>
                        <LogOut className="w-4 h-4 mr-2" />
                        Sign out
                      </DropdownMenuItem>
                    </>
                  ) : (
                    <DropdownMenuItem onClick={() => {/* Trigger login */}}>
                      <UserIcon className="w-4 h-4 mr-2" />
                      Sign In
                    </DropdownMenuItem>
                  )}
                </DropdownMenuContent>
              </DropdownMenu>
            </nav>
          </div>
        </div>
      </header>

      {/* Settings Modal */}
      <SettingsModal open={settingsOpen} onOpenChange={setSettingsOpen} />
    </>
  );
}
