import { Sun, Moon } from "lucide-react";
import { useTheme } from "@/contexts/ThemeContext";
import { Button } from "@/components/ui/button";

export function ThemeSwitcher() {
  const { theme, toggleTheme } = useTheme();

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={toggleTheme}
      className={`rounded-full h-8 w-8 p-0 transition-all duration-300 ${
        theme === "dark"
          ? "text-amber-400 hover:text-amber-300 hover:bg-amber-500/10"
          : "text-amber-600 hover:text-amber-700 hover:bg-amber-500/10"
      }`}
    >
      {theme === "dark" ? (
        <Moon className="w-4 h-4" />
      ) : (
        <Sun className="w-4 h-4" />
      )}
    </Button>
  );
}
