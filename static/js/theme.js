/**
 * ============================================================================
 * NEXUS - Dark Theme Initialization
 * ============================================================================
 * 
 * Simple dark-mode-only initialization script.
 * No theme switching functionality - dark mode is always active.
 * 
 * Version: 2.0 (January 2026)
 * ============================================================================
 */

(function() {
  'use strict';
  
  /**
   * Initialize dark theme
   * Ensures the HTML element has the 'dark' class
   */
  function initDarkTheme() {
    const htmlElement = document.documentElement;
    
    // Remove any light mode class and ensure dark is set
    htmlElement.classList.remove('light');
    htmlElement.classList.add('dark');
  }
  
  /**
   * Remove any theme toggle buttons from the DOM
   * since we no longer support theme switching
   */
  function removeThemeToggles() {
    const toggleButtons = document.querySelectorAll('[data-theme-toggle]');
    toggleButtons.forEach(button => {
      button.style.display = 'none';
    });
  }
  
  // Initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      initDarkTheme();
      removeThemeToggles();
    });
  } else {
    initDarkTheme();
    removeThemeToggles();
  }
  
  // Also run immediately to prevent flash
  initDarkTheme();
})();