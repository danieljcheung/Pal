import { useState, useCallback, useEffect, useRef } from "react";
import { getCurrentWindow } from "@tauri-apps/api/window";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import ChatContainer from "./components/ChatContainer";
import Menu from "./components/Menu";
import BrainPanel from "./components/BrainPanel";
import SettingsPanel from "./components/SettingsPanel";
import { useSettings } from "./contexts/SettingsContext";
import "./App.css";

type WindowMode = "full" | "widget" | "floating";

// Hide for 1 hour duration in ms
const HIDE_DURATION = 60 * 60 * 1000;

function App() {
  const [headerVisible, setHeaderVisible] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [windowMode, setWindowMode] = useState<WindowMode>("full");
  const [brainPanelOpen, setBrainPanelOpen] = useState(false);
  const [settingsPanelOpen, setSettingsPanelOpen] = useState(false);
  const hideTimerRef = useRef<number | null>(null);
  const { settings, updateSettings } = useSettings();

  // Listen for mode changes from tray menu
  useEffect(() => {
    const unlisten = listen<string>("mode-changed", (event) => {
      setWindowMode(event.payload as WindowMode);
    });

    return () => {
      unlisten.then((fn) => fn());
    };
  }, []);

  // Set default mode from settings on startup
  useEffect(() => {
    if (settings.default_mode) {
      const mode = settings.default_mode as WindowMode;
      if (mode !== windowMode) {
        setMode(mode);
      }
    }
  }, [settings.default_mode]);

  const handleClose = async () => {
    const window = getCurrentWindow();
    await window.close();
  };

  const handleMinimize = async () => {
    const window = getCurrentWindow();
    await window.minimize();
  };

  const handleHamburgerClick = () => {
    setMenuOpen((prev) => !prev);
  };

  const handleMenuClose = useCallback(() => {
    setMenuOpen(false);
  }, []);

  // Set window mode via Tauri command
  const setMode = useCallback(async (mode: WindowMode) => {
    try {
      await invoke("set_window_mode", { mode });
      setWindowMode(mode);
    } catch (err) {
      console.error("Failed to set window mode:", err);
    }
  }, []);

  // Menu action handlers
  const handleSelectMode = useCallback((mode: WindowMode) => {
    setMode(mode);
  }, [setMode]);

  const handleOpenBrain = useCallback(() => {
    setBrainPanelOpen(true);
  }, []);

  const handleOpenSettings = useCallback(() => {
    setSettingsPanelOpen(true);
  }, []);

  const handleHide = useCallback(async () => {
    // Hide window for 1 hour
    try {
      await invoke("hide_window");

      // Clear any existing timer
      if (hideTimerRef.current) {
        clearTimeout(hideTimerRef.current);
      }

      // Set timer to show window after 1 hour
      hideTimerRef.current = window.setTimeout(async () => {
        try {
          await invoke("show_window");
        } catch (err) {
          console.error("Failed to show window:", err);
        }
      }, HIDE_DURATION);
    } catch (err) {
      console.error("Failed to hide window:", err);
    }
  }, []);

  const handleQuit = useCallback(async () => {
    const window = getCurrentWindow();
    await window.close();
  }, []);

  // Right-click to open menu (only in full mode)
  const handleContextMenu = (e: React.MouseEvent) => {
    e.preventDefault();
    if (windowMode === "full") {
      setMenuOpen(true);
    }
  };

  // Click to expand from compact modes
  const handleExpandClick = () => {
    if (windowMode === "floating") {
      setMode("widget");
    } else if (windowMode === "widget") {
      setMode("full");
    }
  };

  // Render based on mode
  const renderContent = () => {
    if (windowMode === "floating") {
      return (
        <div className="app-floating" onClick={handleExpandClick}>
          <ChatContainer
            initialMessage=""
            mode="floating"
          />
        </div>
      );
    }

    if (windowMode === "widget") {
      return (
        <div className="app-widget" onClick={handleExpandClick}>
          <ChatContainer
            initialMessage="Hi! Click to chat..."
            mode="widget"
          />
        </div>
      );
    }

    // Full mode
    return (
      <>
        {/* Header with hamburger and window controls */}
        <header className={`app-header ${headerVisible || menuOpen ? "app-header--visible" : ""}`}>
          <button
            className={`hamburger-btn ${menuOpen ? "hamburger-btn--active" : ""}`}
            onClick={handleHamburgerClick}
            title="Menu"
          >
            <span></span>
            <span></span>
            <span></span>
          </button>

          <div className="window-controls">
            <button
              className="window-btn window-btn--minimize"
              onClick={handleMinimize}
              title="Minimize"
            />
            <button
              className="window-btn window-btn--close"
              onClick={handleClose}
              title="Close"
            />
          </div>
        </header>

        {/* Dropdown menu */}
        <Menu
          isOpen={menuOpen}
          onClose={handleMenuClose}
          onSelectMode={handleSelectMode}
          onOpenBrain={handleOpenBrain}
          onOpenSettings={handleOpenSettings}
          onHide={handleHide}
          onQuit={handleQuit}
          currentMode={windowMode}
        />

        {/* Brain panel */}
        <BrainPanel
          isOpen={brainPanelOpen}
          onClose={() => setBrainPanelOpen(false)}
        />

        {/* Settings panel */}
        <SettingsPanel
          isOpen={settingsPanelOpen}
          onClose={() => setSettingsPanelOpen(false)}
          onSettingsChange={updateSettings}
        />

        {/* Main content */}
        <main className="app-content">
          <ChatContainer mode="full" />
        </main>
      </>
    );
  };

  return (
    <div
      className={`app app--${windowMode}`}
      onMouseEnter={() => windowMode === "full" && setHeaderVisible(true)}
      onMouseLeave={() => {
        setHeaderVisible(false);
      }}
      onContextMenu={handleContextMenu}
    >
      {renderContent()}
    </div>
  );
}

export default App;
