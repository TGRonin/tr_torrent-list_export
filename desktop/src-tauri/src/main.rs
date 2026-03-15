#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::{Arc, Mutex};
use tauri::{Manager, WindowEvent};

fn pick_port() -> u16 {
    portpicker::pick_unused_port().unwrap_or(38081)
}

fn repo_root() -> std::io::Result<PathBuf> {
    let current = std::env::current_dir()?;
    Ok(current)
}

fn start_backend(port: u16) -> std::io::Result<Child> {
    let root = repo_root()?;
    let backend_dir = root.join("backend");
    let config_dir = root.join("config");
    let python = "python";
    let mut cmd = Command::new(python);
    cmd.current_dir(backend_dir)
        .env("TR_CONFIG_DIR", config_dir.to_string_lossy().to_string())
        .arg("-m")
        .arg("uvicorn")
        .arg("backend.app:app")
        .arg("--host")
        .arg("127.0.0.1")
        .arg("--port")
        .arg(port.to_string())
        .arg("--workers")
        .arg("1")
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null());
    cmd.spawn()
}

fn main() {
    let port = if cfg!(debug_assertions) { 8000 } else { pick_port() };

    let backend_process = Arc::new(Mutex::new(start_backend(port).ok()));

    tauri::Builder::default()
        .setup(move |app| {
            let window = app.get_window("main").unwrap();
            let url = if cfg!(debug_assertions) {
                format!("http://127.0.0.1:5173?port={}", port)
            } else {
                format!("index.html?port={}", port)
            };
            window.eval(&format!("window.location.replace('{}')", url))?;
            Ok(())
        })
        .on_window_event({
            let backend_process = backend_process.clone();
            move |event| {
                if let WindowEvent::CloseRequested { .. } = event.event() {
                    if let Ok(mut guard) = backend_process.lock() {
                        if let Some(child) = guard.as_mut() {
                            let _ = child.kill();
                        }
                    }
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
