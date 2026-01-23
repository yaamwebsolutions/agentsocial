import { Bot, Home, Users, Bell, Settings, MoreVertical } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useNavigate, useLocation } from "react-router-dom";
import { CommandPalette } from "./CommandPalette";
import { ThemeSwitcher } from "./ThemeSwitcher";
import { useAgents } from "@/hooks/useApi";
import { useTheme } from "@/contexts/ThemeContext";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export function Header() {
  const navigate = useNavigate();
  const location = useLocation();
  const { agents } = useAgents();
  const { theme } = useTheme();

  const handleCreatePost = (text: string) => {
    // Scroll to composer and set text
    const composer = document.getElementById("composer-textarea") as HTMLTextAreaElement;
    if (composer) {
      composer.value = text;
      composer.focus();
      // Trigger input event to update state
      composer.dispatchEvent(new Event("input", { bubbles: true }));
    }
  };

  const handleSearch = (query: string) => {
    navigate(`/?search=${encodeURIComponent(query)}`);
  };

  const isGolden = theme === "golden";

  return (
    <header className="sticky top-0 z-50 bg-background/80 backdrop-blur-xl border-b border-border/50 shadow-sm">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div
            className="flex items-center gap-3 cursor-pointer group"
            onClick={() => navigate("/")}
          >
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center shadow-lg transition-all duration-300 ${
              isGolden
                ? "bg-gradient-to-br from-amber-400 via-yellow-500 to-amber-600 group-hover:shadow-amber-500/30"
                : "bg-gradient-to-br from-blue-400 to-blue-600 group-hover:shadow-blue-500/30"
            } group-hover:scale-105 group-hover:shadow-lg`}>
              <Bot className="w-6 h-6 text-white" />
            </div>
            <span className={`font-bold text-xl hidden sm:block bg-gradient-to-r bg-clip-text text-transparent ${
              isGolden
                ? "from-amber-400 via-yellow-400 to-amber-500"
                : "from-blue-400 to-purple-500"
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
          <nav className="flex items-center gap-2">
            <Button
              variant={location.pathname === "/" ? "secondary" : "ghost"}
              size="sm"
              onClick={() => navigate("/")}
              className="rounded-full font-medium"
            >
              <Home className="w-4 h-4" />
              <span className="hidden sm:inline ml-2">Home</span>
            </Button>
            <Button
              variant={location.pathname === "/agents" ? "secondary" : "ghost"}
              size="sm"
              onClick={() => navigate("/agents")}
              className="rounded-full font-medium"
            >
              <Users className="w-4 h-4" />
              <span className="hidden sm:inline ml-2">Agents</span>
            </Button>

            {/* Theme Switcher */}
            <div className="hidden md:block">
              <ThemeSwitcher />
            </div>

            {/* Mobile Menu */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm" className="rounded-full md:hidden">
                  <MoreVertical className="w-4 h-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                <DropdownMenuItem onClick={() => navigate("/")}>
                  <Home className="w-4 h-4 mr-2" />
                  Home
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => navigate("/agents")}>
                  <Users className="w-4 h-4 mr-2" />
                  Agents
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => {}}>
                  <Settings className="w-4 h-4 mr-2" />
                  Settings
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>

            {/* Desktop Actions */}
            <div className="hidden md:flex items-center gap-1 ml-1">
              <Button variant="ghost" size="sm" className="rounded-full">
                <Bell className="w-4 h-4" />
              </Button>
              <Button variant="ghost" size="sm" className="rounded-full">
                <Settings className="w-4 h-4" />
              </Button>
            </div>
          </nav>
        </div>
      </div>
    </header>
  );
}
