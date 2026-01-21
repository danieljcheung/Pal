import { useState, useCallback } from "react";
import { getCurrentWindow } from "@tauri-apps/api/window";
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

  // Menu action handlers (placeholders for now)
  const handleSelectMode = useCallback((mode: WindowMode) => {
    setWindowMode(mode);
    console.log(`Switched to ${mode} mode`);
    // TODO: Implement window mode switching
  }, []);

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

  // Right-click to open menu
  const handleContextMenu = (e: React.MouseEvent) => {
    e.preventDefault();
    setMenuOpen(true);
  };

  return (
    <div
      className="app"
      onMouseEnter={() => setHeaderVisible(true)}
      onMouseLeave={() => {
        setHeaderVisible(false);
        // Don't close menu on mouse leave - let click outside handle it
      }}
      onContextMenu={handleContextMenu}
    >
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
        <ChatContainer initialMessage="Hi! How can I help you today?" />
      </main>
    </div>
  );
}

export default App;
