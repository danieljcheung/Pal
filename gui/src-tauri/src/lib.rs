use std::fs;
use std::path::PathBuf;
use std::sync::Mutex;
use tauri::{
    Emitter, LogicalSize, Manager, Size, WebviewWindow,
    menu::{Menu, MenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
};
use tauri_plugin_global_shortcut::{Code, GlobalShortcutExt, Modifiers, Shortcut};
use serde::{Deserialize, Serialize};

// Settings struct
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Settings {
    pub pal_name: String,
    pub owner_name: String,
    pub sounds_enabled: bool,
    pub notifications_enabled: bool,
    pub default_mode: String,
    pub api_key: String,
}

impl Default for Settings {
    fn default() -> Self {
        Self {
            pal_name: "Pal".to_string(),
            owner_name: "".to_string(),
            sounds_enabled: true,
            notifications_enabled: true,
            default_mode: "full".to_string(),
            api_key: "".to_string(),
        }
    }
}

// Global state for hide timer
struct HideState {
    hide_until: Option<std::time::Instant>,
}

// Get config directory
fn get_config_dir() -> PathBuf {
    dirs::config_dir()
        .unwrap_or_else(|| PathBuf::from("."))
        .join("Pal")
}

// Get config file path
fn get_config_path() -> PathBuf {
    get_config_dir().join("settings.json")
}

// Load settings from file
fn load_settings_from_file() -> Settings {
    let path = get_config_path();
    if path.exists() {
        if let Ok(content) = fs::read_to_string(&path) {
            if let Ok(settings) = serde_json::from_str(&content) {
                return settings;
            }
        }
    }
    Settings::default()
}

// Save settings to file
fn save_settings_to_file(settings: &Settings) -> Result<(), String> {
    let dir = get_config_dir();
    fs::create_dir_all(&dir).map_err(|e| e.to_string())?;

    let path = get_config_path();
    let content = serde_json::to_string_pretty(settings).map_err(|e| e.to_string())?;
    fs::write(&path, content).map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[tauri::command]
async fn set_window_mode(window: WebviewWindow, mode: &str) -> Result<(), String> {
    apply_window_mode(&window, mode)
}

fn apply_window_mode(window: &WebviewWindow, mode: &str) -> Result<(), String> {
    match mode {
        "full" => {
            window.set_size(Size::Logical(LogicalSize::new(400.0, 500.0)))
                .map_err(|e| e.to_string())?;
            window.set_always_on_top(false)
                .map_err(|e| e.to_string())?;
            window.set_decorations(false)
                .map_err(|e| e.to_string())?;
            window.set_resizable(true)
                .map_err(|e| e.to_string())?;
        },
        "widget" => {
            window.set_size(Size::Logical(LogicalSize::new(220.0, 180.0)))
                .map_err(|e| e.to_string())?;
            window.set_always_on_top(true)
                .map_err(|e| e.to_string())?;
            window.set_decorations(false)
                .map_err(|e| e.to_string())?;
            window.set_resizable(false)
                .map_err(|e| e.to_string())?;
        },
        "floating" => {
            window.set_size(Size::Logical(LogicalSize::new(150.0, 100.0)))
                .map_err(|e| e.to_string())?;
            window.set_always_on_top(true)
                .map_err(|e| e.to_string())?;
            window.set_decorations(false)
                .map_err(|e| e.to_string())?;
            window.set_resizable(false)
                .map_err(|e| e.to_string())?;
        },
        _ => return Err(format!("Unknown mode: {}", mode)),
    }
    Ok(())
}

#[tauri::command]
fn load_settings() -> Settings {
    load_settings_from_file()
}

#[tauri::command]
fn save_settings(settings: Settings) -> Result<(), String> {
    save_settings_to_file(&settings)
}

#[tauri::command]
async fn hide_window(window: WebviewWindow) -> Result<(), String> {
    window.hide().map_err(|e| e.to_string())
}

#[tauri::command]
async fn show_window(window: WebviewWindow) -> Result<(), String> {
    window.show().map_err(|e| e.to_string())?;
    window.set_focus().map_err(|e| e.to_string())
}

#[tauri::command]
async fn send_notification(
    app: tauri::AppHandle,
    title: String,
    body: String,
) -> Result<(), String> {
    use tauri_plugin_notification::NotificationExt;

    app.notification()
        .builder()
        .title(&title)
        .body(&body)
        .show()
        .map_err(|e| e.to_string())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_global_shortcut::Builder::new().build())
        .plugin(tauri_plugin_fs::init())
        .manage(Mutex::new(HideState { hide_until: None }))
        .invoke_handler(tauri::generate_handler![
            greet,
            set_window_mode,
            load_settings,
            save_settings,
            hide_window,
            show_window,
            send_notification,
        ])
        .setup(|app| {
            // Build tray menu
            let show = MenuItem::with_id(app, "show", "Show Pal", true, None::<&str>)?;
            let full = MenuItem::with_id(app, "full", "Full window", true, None::<&str>)?;
            let widget = MenuItem::with_id(app, "widget", "Widget mode", true, None::<&str>)?;
            let floating = MenuItem::with_id(app, "floating", "Floating mode", true, None::<&str>)?;
            let quit = MenuItem::with_id(app, "quit", "Quit", true, None::<&str>)?;

            let menu = Menu::with_items(app, &[&show, &full, &widget, &floating, &quit])?;

            // Build tray icon
            let _tray = TrayIconBuilder::new()
                .icon(app.default_window_icon().unwrap().clone())
                .tooltip("Pal")
                .menu(&menu)
                .show_menu_on_left_click(false)
                .on_tray_icon_event(|tray, event| {
                    match event {
                        TrayIconEvent::Click {
                            button: MouseButton::Left,
                            button_state: MouseButtonState::Up,
                            ..
                        } => {
                            // Show window on left click
                            let app = tray.app_handle();
                            if let Some(window) = app.get_webview_window("main") {
                                let _ = window.show();
                                let _ = window.set_focus();
                            }
                        }
                        _ => {}
                    }
                })
                .on_menu_event(|app, event| {
                    match event.id.as_ref() {
                        "show" => {
                            if let Some(window) = app.get_webview_window("main") {
                                let _ = window.show();
                                let _ = window.set_focus();
                            }
                        }
                        "full" => {
                            if let Some(window) = app.get_webview_window("main") {
                                let _ = window.show();
                                let _ = window.set_focus();
                                let _ = apply_window_mode(&window, "full");
                                let _ = window.emit("mode-changed", "full");
                            }
                        }
                        "widget" => {
                            if let Some(window) = app.get_webview_window("main") {
                                let _ = window.show();
                                let _ = window.set_focus();
                                let _ = apply_window_mode(&window, "widget");
                                let _ = window.emit("mode-changed", "widget");
                            }
                        }
                        "floating" => {
                            if let Some(window) = app.get_webview_window("main") {
                                let _ = window.show();
                                let _ = window.set_focus();
                                let _ = apply_window_mode(&window, "floating");
                                let _ = window.emit("mode-changed", "floating");
                            }
                        }
                        "quit" => {
                            std::process::exit(0);
                        }
                        _ => {}
                    }
                })
                .build(app)?;

            // Register global shortcut (Ctrl+Shift+P / Cmd+Shift+P)
            let shortcut = Shortcut::new(Some(Modifiers::CONTROL | Modifiers::SHIFT), Code::KeyP);

            let app_handle = app.handle().clone();
            app.global_shortcut().on_shortcut(shortcut, move |_app, _shortcut, _event| {
                if let Some(window) = app_handle.get_webview_window("main") {
                    // Check if window is visible and focused
                    let is_visible = window.is_visible().unwrap_or(false);
                    let is_focused = window.is_focused().unwrap_or(false);

                    if !is_visible {
                        // Hidden -> show
                        let _ = window.show();
                        let _ = window.set_focus();
                    } else if is_focused {
                        // Focused -> hide
                        let _ = window.hide();
                    } else {
                        // Visible but not focused -> focus
                        let _ = window.set_focus();
                    }
                }
            })?;

            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                // Don't quit, hide to tray
                let _ = window.hide();
                api.prevent_close();
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
