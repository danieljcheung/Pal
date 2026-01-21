import { useState } from "react";
import { getCurrentWindow } from "@tauri-apps/api/window";
import Face from "./components/Face";
import "./App.css";

function App() {
  const [input, setInput] = useState("");
  const [message, setMessage] = useState("Hello from Pal");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      // Placeholder - will connect to Python backend later
      setMessage(`You said: "${input}"`);
      setInput("");
    }
  };

  const handleClose = async () => {
    const window = getCurrentWindow();
    await window.close();
  };

  const handleMinimize = async () => {
    const window = getCurrentWindow();
    await window.minimize();
  };

  return (
    <div className="app">
      {/* Custom titlebar */}
      <div className="titlebar">
        <span className="titlebar-title">Pal</span>
        <div className="titlebar-controls">
          <button
            className="titlebar-btn minimize"
            onClick={handleMinimize}
            title="Minimize"
          />
          <button
            className="titlebar-btn close"
            onClick={handleClose}
            title="Close"
          />
        </div>
      </div>

      {/* Main content */}
      <div className="content">
        <Face mood="curious" />
        <p className="message">{message}</p>
      </div>

      {/* Input area */}
      <div className="input-area">
        <form className="input-container" onSubmit={handleSubmit}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Say something..."
            autoFocus
          />
          <button type="submit">Send</button>
        </form>
      </div>
    </div>
  );
}

export default App;
