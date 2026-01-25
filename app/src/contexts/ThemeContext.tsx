import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

export type Theme = "light" | "dark";

interface ThemeContextType {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const themes = {
  // Apple-style Light Theme with Golden Nuances
  light: {
    background: "0 0% 98%",           // Pure white/cream
    foreground: "40 10% 10%",          // Soft black
    card: "40 30% 99%",                // Warm white cards
    "card-foreground": "40 10% 10%",   // Dark text
    popover: "40 30% 99%",             // Warm white popover
    "popover-foreground": "40 10% 10%",
    primary: "38 90% 55%",             // Elegant gold
    "primary-foreground": "0 0% 100%", // White text on gold
    secondary: "40 20% 95%",           // Subtle warm gray
    "secondary-foreground": "40 10% 15%",
    muted: "40 15% 92%",               // Muted background
    "muted-foreground": "40 10% 40%",  // Muted text
    accent: "38 80% 92%",              // Light gold accent
    "accent-foreground": "40 10% 10%",
    destructive: "0 80% 55%",          // Elegant red
    "destructive-foreground": "0 0% 100%",
    border: "40 20% 88%",              // Subtle border
    input: "40 20% 88%",               // Input border
    ring: "38 90% 55%",                // Gold focus ring
  },
  // Elegant Dark Theme with Golden Accents
  dark: {
    background: "40 15% 8%",           // Rich dark background
    foreground: "40 20% 96%",          // Warm white
    card: "40 20% 12%",                // Dark cards
    "card-foreground": "40 20% 96%",   // Light text
    popover: "40 20% 12%",             // Dark popover
    "popover-foreground": "40 20% 96%",
    primary: "38 95% 58%",             // Bright gold
    "primary-foreground": "40 15% 8%", // Dark text on gold
    secondary: "40 15% 18%",           // Dark secondary
    "secondary-foreground": "40 20% 90%",
    muted: "40 15% 18%",               // Dark muted
    "muted-foreground": "40 10% 60%",  // Grayed text
    accent: "38 70% 30%",              // Dark gold accent
    "accent-foreground": "40 20% 96%",
    destructive: "0 75% 55%",          // Red
    "destructive-foreground": "40 20% 96%",
    border: "40 20% 20%",              // Dark border
    input: "40 20% 20%",               // Input border
    ring: "38 95% 58%",                // Gold focus ring
  },
};

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(() => {
    const stored = localStorage.getItem("theme") as Theme;
    return stored || "light";
  });

  useEffect(() => {
    const root = document.documentElement;
    const themeColors = themes[theme];

    // Apply theme colors
    Object.entries(themeColors).forEach(([key, value]) => {
      root.style.setProperty(`--${key}`, value);
    });

    // Manage dark mode class
    if (theme === "dark") {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }

    localStorage.setItem("theme", theme);
  }, [theme]);

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
  };

  const toggleTheme = () => {
    setThemeState((prev) => (prev === "light" ? "dark" : "light"));
  };

  return (
    <ThemeContext.Provider value={{ theme, setTheme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within ThemeProvider");
  }
  return context;
}
