import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from "react";
import { invoke } from "@tauri-apps/api/core";

export interface Settings {
  pal_name: string;
  owner_name: string;
  sounds_enabled: boolean;
  notifications_enabled: boolean;
  default_mode: string;
  api_key: string;
}

const DEFAULT_SETTINGS: Settings = {
  pal_name: "Pal",
  owner_name: "",
  sounds_enabled: true,
  notifications_enabled: true,
  default_mode: "full",
  api_key: "",
};

interface SettingsContextType {
  settings: Settings;
  loading: boolean;
  updateSettings: (newSettings: Settings) => void;
  reloadSettings: () => Promise<void>;
}

const SettingsContext = createContext<SettingsContextType | null>(null);

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [settings, setSettings] = useState<Settings>(DEFAULT_SETTINGS);
  const [loading, setLoading] = useState(true);

  const loadSettings = useCallback(async () => {
    try {
      const loaded = await invoke<Settings>("load_settings");
      setSettings(loaded);
    } catch (err) {
      console.error("Failed to load settings:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSettings();
  }, [loadSettings]);

  const updateSettings = useCallback((newSettings: Settings) => {
    setSettings(newSettings);
  }, []);

  const reloadSettings = useCallback(async () => {
    await loadSettings();
  }, [loadSettings]);

  return (
    <SettingsContext.Provider value={{ settings, loading, updateSettings, reloadSettings }}>
      {children}
    </SettingsContext.Provider>
  );
}

export function useSettings() {
  const context = useContext(SettingsContext);
  if (!context) {
    throw new Error("useSettings must be used within a SettingsProvider");
  }
  return context;
}
