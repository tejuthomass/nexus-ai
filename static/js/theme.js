/**
 * Theme Switching System
 * Manages light/dark mode with system preference detection
 * No database persistence - uses browser's theme preference detection
 */

class ThemeManager {
  constructor() {
    this.THEME_KEY = 'nexus-theme-preference';
    this.DARK_THEME = 'dark';
    this.LIGHT_THEME = 'light';
    this.SYSTEM_THEME = 'system';
    
    // Initialize theme on page load
    this.initTheme();
    
    // Listen for system preference changes
    this.listenToSystemPreference();
    
    // Listen for theme toggle button clicks
    this.setupToggleListener();
  }

  /**
   * Initialize theme based on:
   * 1. Browser's localStorage (if exists)
   * 2. System preference (if not stored)
   * 3. Default to dark mode
   */
  initTheme() {
    // Try to get stored preference (only current session, not persistent)
    const storedTheme = sessionStorage.getItem(this.THEME_KEY);
    
    if (storedTheme) {
      // Use stored preference from current session
      this.setTheme(storedTheme);
    } else {
      // Use system preference or default to dark
      const systemPreference = this.getSystemPreference();
      this.setTheme(systemPreference);
      sessionStorage.setItem(this.THEME_KEY, systemPreference);
    }
  }

  /**
   * Get system preference from OS/browser
   */
  getSystemPreference() {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
      return this.LIGHT_THEME;
    }
    return this.DARK_THEME;
  }

  /**
   * Set the current theme
   */
  setTheme(theme) {
    const htmlElement = document.documentElement;
    
    if (theme === this.LIGHT_THEME) {
      htmlElement.classList.remove('dark');
      htmlElement.classList.add('light');
    } else {
      htmlElement.classList.remove('light');
      htmlElement.classList.add('dark');
    }
    
    // Update toggle button state if it exists
    this.updateToggleButton(theme);
    
    // Store in session storage (not persistent across sessions)
    sessionStorage.setItem(this.THEME_KEY, theme);
  }

  /**
   * Get current theme
   */
  getTheme() {
    return document.documentElement.classList.contains('dark') ? this.DARK_THEME : this.LIGHT_THEME;
  }

  /**
   * Toggle between light and dark theme
   */
  toggleTheme() {
    const currentTheme = this.getTheme();
    const newTheme = currentTheme === this.DARK_THEME ? this.LIGHT_THEME : this.DARK_THEME;
    this.setTheme(newTheme);
  }

  /**
   * Listen to system preference changes
   */
  listenToSystemPreference() {
    if (window.matchMedia) {
      const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
      
      // Modern browsers
      if (darkModeQuery.addEventListener) {
        darkModeQuery.addEventListener('change', (e) => {
          // Only change if user hasn't manually set a preference in this session
          const storedTheme = sessionStorage.getItem(this.THEME_KEY);
          if (!storedTheme) {
            const newTheme = e.matches ? this.DARK_THEME : this.LIGHT_THEME;
            this.setTheme(newTheme);
          }
        });
      }
      // Legacy browsers
      else if (darkModeQuery.addListener) {
        darkModeQuery.addListener((e) => {
          const storedTheme = sessionStorage.getItem(this.THEME_KEY);
          if (!storedTheme) {
            const newTheme = e.matches ? this.DARK_THEME : this.LIGHT_THEME;
            this.setTheme(newTheme);
          }
        });
      }
    }
  }

  /**
   * Setup event listener for theme toggle buttons
   */
  setupToggleListener() {
    // Find all theme toggle buttons
    const toggleButtons = document.querySelectorAll('[data-theme-toggle]');
    
    toggleButtons.forEach(button => {
      button.addEventListener('click', () => {
        this.toggleTheme();
      });
    });
  }

  /**
   * Update toggle button visual state
   */
  updateToggleButton(theme) {
    const toggleButtons = document.querySelectorAll('[data-theme-toggle]');
    
    toggleButtons.forEach(button => {
      // Find the icon inside the button
      const icon = button.querySelector('i');
      
      if (theme === this.LIGHT_THEME) {
        // Show moon icon for light mode (to switch to dark)
        if (icon) {
          icon.classList.remove('fa-sun');
          icon.classList.add('fa-moon');
        }
        button.setAttribute('aria-label', 'Switch to dark mode');
      } else {
        // Show sun icon for dark mode (to switch to light)
        if (icon) {
          icon.classList.remove('fa-moon');
          icon.classList.add('fa-sun');
        }
        button.setAttribute('aria-label', 'Switch to light mode');
      }
    });
  }

  /**
   * Manual theme setter (for preference changes)
   */
  setManualTheme(theme) {
    if (theme === this.LIGHT_THEME || theme === this.DARK_THEME) {
      this.setTheme(theme);
    }
  }
}

// Initialize theme manager when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.themeManager = new ThemeManager();
  });
} else {
  window.themeManager = new ThemeManager();
}
