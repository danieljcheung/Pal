use tauri::{
    LogicalSize, Manager, Size, WebviewWindow,
    menu::{Menu, MenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
};

// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/
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

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![greet, set_window_mode])
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
                            }
                        }
                        "widget" => {
                            if let Some(window) = app.get_webview_window("main") {
                                let _ = window.show();
                                let _ = window.set_focus();
                                let _ = apply_window_mode(&window, "widget");
                            }
                        }
                        "floating" => {
                            if let Some(window) = app.get_webview_window("main") {
                                let _ = window.show();
                                let _ = window.set_focus();
                                let _ = apply_window_mode(&window, "floating");
                            }
                        }
                        "quit" => {
                            std::process::exit(0);
                        }
                        _ => {}
                    }
                })
                .build(app)?;

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
