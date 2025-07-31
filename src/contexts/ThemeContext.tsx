import React, { createContext, useContext, useEffect, useState } from 'react';

type Theme = 'light' | 'dark' | 'system';

interface ThemeContextType {
  theme: Theme;
  actualTheme: 'light' | 'dark'; // The resolved theme (system resolves to light/dark)
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

interface ThemeProviderProps {
  children: React.ReactNode;
  defaultTheme?: Theme;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({
  children,
  defaultTheme = 'system'
}) => {
  const [theme, setThemeState] = useState<Theme>(defaultTheme);
  const [actualTheme, setActualTheme] = useState<'light' | 'dark'>('light');

  // Function to get system preference
  const getSystemTheme = (): 'light' | 'dark' => {
    if (typeof window !== 'undefined') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    return 'light';
  };

  // Function to resolve the actual theme based on current setting
  const resolveTheme = (currentTheme: Theme): 'light' | 'dark' => {
    if (currentTheme === 'system') {
      return getSystemTheme();
    }
    return currentTheme;
  };

  // Initialize theme from localStorage or default
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as Theme;
    if (savedTheme && ['light', 'dark', 'system'].includes(savedTheme)) {
      setThemeState(savedTheme);
    }
  }, []);

  // Update actual theme when theme changes or system preference changes
  useEffect(() => {
    const resolved = resolveTheme(theme);
    setActualTheme(resolved);

    // Apply theme to document
    const root = document.documentElement;
    if (resolved === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }

    // Save to localStorage
    localStorage.setItem('theme', theme);
  }, [theme]);

  // Listen for system theme changes
  useEffect(() => {
    if (theme === 'system') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

      const handleChange = () => {
        const resolved = resolveTheme(theme);
        setActualTheme(resolved);

        const root = document.documentElement;
        if (resolved === 'dark') {
          root.classList.add('dark');
        } else {
          root.classList.remove('dark');
        }
      };

      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    }
  }, [theme]);

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
  };

  const toggleTheme = () => {
    if (theme === 'light') {
      setTheme('dark');
    } else if (theme === 'dark') {
      setTheme('system');
    } else {
      setTheme('light');
    }
  };

  const value: ThemeContextType = {
    theme,
    actualTheme,
    setTheme,
    toggleTheme,
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

// Hook for getting theme-aware classes
export const useThemeClasses = () => {
  const { actualTheme } = useTheme();

  return {
    // Background classes
    bg: {
      primary: actualTheme === 'dark' ? 'bg-gray-900' : 'bg-white',
      secondary: actualTheme === 'dark' ? 'bg-gray-800' : 'bg-gray-50',
      tertiary: actualTheme === 'dark' ? 'bg-gray-700' : 'bg-gray-100',
    },

    // Text classes
    text: {
      primary: actualTheme === 'dark' ? 'text-white' : 'text-gray-900',
      secondary: actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-600',
      tertiary: actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-500',
    },

    // Border classes
    border: {
      primary: actualTheme === 'dark' ? 'border-gray-600' : 'border-gray-200',
      secondary: actualTheme === 'dark' ? 'border-gray-700' : 'border-gray-300',
    },

    // Interactive classes
    hover: {
      bg: actualTheme === 'dark' ? 'hover:bg-gray-700' : 'hover:bg-gray-50',
    },

    // Card/panel classes
    card: actualTheme === 'dark'
      ? 'bg-gray-800 border-gray-700'
      : 'bg-white border-gray-200',
  };
};
