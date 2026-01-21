import { useState, useCallback } from "react";
import { getCurrentWindow } from "@tauri-apps/api/window";
import { invoke } from "@tauri-apps/api/core";
import ChatContainer from "./components/ChatContainer";
import Menu from "./components/Menu";
import "./App.css";

type WindowMode = "full" | "widget" | "floating";

function App() {
  const [headerVisible, setHeaderVisible] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [windowMode, setWindowMode] = useState<WindowMode>("full");

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

  const handleOpenHistory = useCallback(() => {
    console.log("Opening history...");
    // TODO: Implement history panel
  }, []);

  const handleOpenBrain = useCallback(() => {
    console.log("Opening Pal's Brain...");
    // TODO: Implement brain visualization
  }, []);

  const handleOpenSettings = useCallback(() => {
    console.log("Opening settings...");
    // TODO: Implement settings panel
  }, []);

  const handleHide = useCallback(() => {
    console.log("Hiding for 1 hour...");
    // TODO: Implement hide functionality
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
          onOpenHistory={handleOpenHistory}
          onOpenBrain={handleOpenBrain}
          onOpenSettings={handleOpenSettings}
          onHide={handleHide}
          onQuit={handleQuit}
          currentMode={windowMode}
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
