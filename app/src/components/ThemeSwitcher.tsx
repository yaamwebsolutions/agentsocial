import { Moon, Sparkles } from "lucide-react";
import { useTheme } from "@/contexts/ThemeContext";
import { Button } from "@/components/ui/button";

export function ThemeSwitcher() {
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="flex items-center gap-1 bg-muted/50 rounded-full p-1 border border-border/50">
      <Button
        variant="ghost"
        size="sm"
        onClick={() => {
          if (theme !== "blue") toggleTheme();
        }}
        className={`rounded-full px-3 h-7 transition-all duration-300 ${
          theme === "blue"
            ? "bg-blue-500 text-white shadow-lg shadow-blue-500/30"
            : "text-muted-foreground hover:text-foreground"
        }`}
      >
        <Moon className="w-4 h-4" />
      </Button>
      <Button
        variant="ghost"
        size="sm"
        onClick={() => {
          if (theme !== "golden") toggleTheme();
        }}
        className={`rounded-full px-3 h-7 transition-all duration-300 ${
          theme === "golden"
            ? "bg-gradient-to-r from-amber-500 to-yellow-400 text-white shadow-lg shadow-amber-500/30"
            : "text-muted-foreground hover:text-foreground"
        }`}
      >
        <Sparkles className="w-4 h-4" />
      </Button>
    </div>
  );
}
