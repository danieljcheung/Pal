import { useState } from "react";
import { getCurrentWindow } from "@tauri-apps/api/window";
import ChatContainer from "./components/ChatContainer";
import "./App.css";

function App() {
  const [menuVisible, setMenuVisible] = useState(false);

  const handleClose = async () => {
    const window = getCurrentWindow();
    await window.close();
  };

  const handleMinimize = async () => {
    const window = getCurrentWindow();
    await window.minimize();
  };

  return (
    <div
      className="app"
      onMouseEnter={() => setMenuVisible(true)}
      onMouseLeave={() => setMenuVisible(false)}
    >
      {/* Header with hamburger and window controls */}
      <header className={`app-header ${menuVisible ? "app-header--visible" : ""}`}>
        <button className="hamburger-btn" title="Menu">
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

      {/* Main content */}
      <main className="app-content">
        <ChatContainer initialMessage="Hi! How can I help you today?" />
      </main>
    </div>
  );
}

export default App;
