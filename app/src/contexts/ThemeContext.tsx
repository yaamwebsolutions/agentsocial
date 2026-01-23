import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

export type Theme = "blue" | "golden";

interface ThemeContextType {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const themes = {
  blue: {
    background: "222 47% 5%",
    foreground: "210 20% 98%",
    card: "222 47% 8%",
    "card-foreground": "210 20% 98%",
    popover: "222 47% 8%",
    "popover-foreground": "210 20% 98%",
    primary: "217 91% 60%",
    "primary-foreground": "222 47% 5%",
    secondary: "217 19% 27%",
    "secondary-foreground": "210 20% 98%",
    muted: "217 19% 27%",
    "muted-foreground": "215 16% 60%",
    accent: "217 19% 27%",
    "accent-foreground": "210 20% 98%",
    destructive: "0 84% 60%",
    "destructive-foreground": "210 20% 98%",
    border: "217 19% 27%",
    input: "217 19% 27%",
    ring: "217 91% 60%",
  },
  golden: {
    background: "40 20% 8%",
    foreground: "45 30% 97%",
    card: "40 25% 12%",
    "card-foreground": "45 30% 97%",
    popover: "40 25% 12%",
    "popover-foreground": "45 30% 97%",
    primary: "43 96% 56%",
    "primary-foreground": "40 20% 8%",
    secondary: "40 15% 20%",
    "secondary-foreground": "45 30% 97%",
    muted: "40 15% 20%",
    "muted-foreground": "40 10% 60%",
    accent: "35 60% 45%",
    "accent-foreground": "45 30% 97%",
    destructive: "0 84% 60%",
    "destructive-foreground": "45 30% 97%",
    border: "40 20% 25%",
    input: "40 20% 25%",
    ring: "43 96% 56%",
  },
};

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(() => {
    const stored = localStorage.getItem("theme") as Theme;
    return stored || "blue";
  });

  useEffect(() => {
    const root = document.documentElement;
    const themeColors = themes[theme];

    Object.entries(themeColors).forEach(([key, value]) => {
      root.style.setProperty(`--${key}`, value);
    });

    localStorage.setItem("theme", theme);
  }, [theme]);

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
  };

  const toggleTheme = () => {
    setThemeState((prev) => (prev === "blue" ? "golden" : "blue"));
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
