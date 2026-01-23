import { useState, useEffect, useRef } from "react";
import { invoke } from "@tauri-apps/api/core";
import "./SettingsPanel.css";

interface Settings {
  pal_name: string;
  owner_name: string;
  sounds_enabled: boolean;
  notifications_enabled: boolean;
  default_mode: string;
  api_key: string;
}

interface SettingsPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onSettingsChange?: (settings: Settings) => void;
}

const DEFAULT_SETTINGS: Settings = {
  pal_name: "Pal",
  owner_name: "",
  sounds_enabled: true,
  notifications_enabled: true,
  default_mode: "full",
  api_key: "",
};

function SettingsPanel({ isOpen, onClose, onSettingsChange }: SettingsPanelProps) {
  const [settings, setSettings] = useState<Settings>(DEFAULT_SETTINGS);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [showResetConfirm, setShowResetConfirm] = useState(false);
  const [showApiKey, setShowApiKey] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);

  // Load settings when panel opens
  useEffect(() => {
    if (!isOpen) return;

    const loadSettings = async () => {
      setLoading(true);
      try {
        const loaded = await invoke<Settings>("load_settings");
        setSettings(loaded);
      } catch (err) {
        console.error("Failed to load settings:", err);
      } finally {
        setLoading(false);
      }
    };

    loadSettings();
  }, [isOpen]);

  // Close on Escape
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        if (showResetConfirm) {
          setShowResetConfirm(false);
        } else {
          onClose();
        }
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose, showResetConfirm]);

  // Reset state when closing
  useEffect(() => {
    if (!isOpen) {
      setShowResetConfirm(false);
      setShowApiKey(false);
    }
  }, [isOpen]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await invoke("save_settings", { settings });
      onSettingsChange?.(settings);
      onClose();
    } catch (err) {
      console.error("Failed to save settings:", err);
    } finally {
      setSaving(false);
    }
  };

  const handleReset = async () => {
    // Reset Pal's memory by calling Python backend
    try {
      // Delete memory files - this will be done via a new endpoint
      await fetch("http://127.0.0.1:8000/reset-pal", { method: "POST" });
      // Reset settings to default
      setSettings(DEFAULT_SETTINGS);
      await invoke("save_settings", { settings: DEFAULT_SETTINGS });
      setShowResetConfirm(false);
      onClose();
      // Reload page to reset state
      window.location.reload();
    } catch (err) {
      console.error("Failed to reset Pal:", err);
      setShowResetConfirm(false);
    }
  };

  const handleChange = <K extends keyof Settings>(key: K, value: Settings[K]) => {
    setSettings((prev) => ({ ...prev, [key]: value }));
  };

  // Handle backdrop click
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="settings-overlay" onClick={handleBackdropClick}>
      <div ref={panelRef} className="settings-panel">
        {/* Close button */}
        <button className="settings-panel__close" onClick={onClose}>&times;</button>

        <header className="settings-header">
          <h2>Settings</h2>
        </header>

        {loading ? (
          <div className="settings-loading">Loading...</div>
        ) : (
          <div className="settings-content">
            {/* Names Section */}
            <section className="settings-section">
              <h3 className="settings-section__title">Names</h3>

              <div className="settings-field">
                <label className="settings-field__label">Pal's name</label>
                <input
                  type="text"
                  className="settings-field__input"
                  value={settings.pal_name}
                  onChange={(e) => handleChange("pal_name", e.target.value)}
                  placeholder="Pal"
                />
              </div>

              <div className="settings-field">
                <label className="settings-field__label">Your name</label>
                <input
                  type="text"
                  className="settings-field__input"
                  value={settings.owner_name}
                  onChange={(e) => handleChange("owner_name", e.target.value)}
                  placeholder="Your name"
                />
              </div>
            </section>

            {/* Preferences Section */}
            <section className="settings-section">
              <h3 className="settings-section__title">Preferences</h3>

              <div className="settings-field settings-field--toggle">
                <label className="settings-field__label">Sounds</label>
                <button
                  className={`settings-toggle ${settings.sounds_enabled ? "settings-toggle--on" : ""}`}
                  onClick={() => handleChange("sounds_enabled", !settings.sounds_enabled)}
                >
                  <span className="settings-toggle__knob" />
                </button>
              </div>

              <div className="settings-field settings-field--toggle">
                <label className="settings-field__label">Notifications</label>
                <button
                  className={`settings-toggle ${settings.notifications_enabled ? "settings-toggle--on" : ""}`}
                  onClick={() => handleChange("notifications_enabled", !settings.notifications_enabled)}
                >
                  <span className="settings-toggle__knob" />
                </button>
              </div>

              <div className="settings-field">
                <label className="settings-field__label">Default window mode</label>
                <select
                  className="settings-field__select"
                  value={settings.default_mode}
                  onChange={(e) => handleChange("default_mode", e.target.value)}
                >
                  <option value="full">Full window</option>
                  <option value="widget">Widget mode</option>
                  <option value="floating">Floating mode</option>
                </select>
              </div>
            </section>

            {/* Advanced Section */}
            <section className="settings-section">
              <h3 className="settings-section__title">Advanced</h3>

              <div className="settings-field">
                <label className="settings-field__label">API Key</label>
                <div className="settings-field__api-key">
                  <input
                    type={showApiKey ? "text" : "password"}
                    className="settings-field__input"
                    value={settings.api_key}
                    onChange={(e) => handleChange("api_key", e.target.value)}
                    placeholder="sk-..."
                  />
                  <button
                    className="settings-field__toggle-visibility"
                    onClick={() => setShowApiKey(!showApiKey)}
                  >
                    {showApiKey ? "Hide" : "Show"}
                  </button>
                </div>
              </div>
            </section>

            {/* Danger Zone */}
            <section className="settings-section settings-section--danger">
              <h3 className="settings-section__title">Danger Zone</h3>

              <div className="settings-field">
                <p className="settings-field__description">
                  Reset Pal to factory settings. This will erase all memories and start fresh.
                </p>
                <button
                  className="settings-button settings-button--danger"
                  onClick={() => setShowResetConfirm(true)}
                >
                  Reset Pal
                </button>
              </div>
            </section>
          </div>
        )}

        {/* Footer with Save button */}
        <footer className="settings-footer">
          <button className="settings-button settings-button--secondary" onClick={onClose}>
            Cancel
          </button>
          <button
            className="settings-button settings-button--primary"
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? "Saving..." : "Save"}
          </button>
        </footer>

        {/* Reset Confirmation Dialog */}
        {showResetConfirm && (
          <div className="settings-confirm-overlay">
            <div className="settings-confirm">
              <h3>Reset Pal?</h3>
              <p>This will erase all of Pal's memories and start fresh. This cannot be undone.</p>
              <div className="settings-confirm__actions">
                <button
                  className="settings-button settings-button--secondary"
                  onClick={() => setShowResetConfirm(false)}
                >
                  Cancel
                </button>
                <button
                  className="settings-button settings-button--danger"
                  onClick={handleReset}
                >
                  Reset
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default SettingsPanel;
