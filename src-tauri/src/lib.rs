use serde::Serialize;
use std::{net::TcpListener, sync::Mutex};
use tauri::{Manager, State};
use tauri_plugin_shell::{process::CommandChild, ShellExt};

struct BackendState {
    config: BackendConfig,
    child: Mutex<Option<CommandChild>>,
}

#[derive(Clone, Serialize)]
#[serde(rename_all = "camelCase")]
struct BackendConfig {
    base_url: String,
    token: String,
}

#[tauri::command]
fn backend_config(state: State<'_, BackendState>) -> BackendConfig {
    state.config.clone()
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            let listener = TcpListener::bind("127.0.0.1:0")?;
            let port = listener.local_addr()?.port();
            drop(listener);
            let token = uuid::Uuid::new_v4().to_string() + &uuid::Uuid::new_v4().to_string();
            let data_dir = app.path().app_local_data_dir()?;
            std::fs::create_dir_all(&data_dir)?;
            let (mut rx, child) = app
                .shell()
                .sidecar("agentsec-backend")?
                .env("AGENTSEC_API_TOKEN", &token)
                .env("AGENTSEC_PORT", port.to_string())
                .env("AGENTSEC_DATA_DIR", data_dir)
                .spawn()?;
            tauri::async_runtime::spawn(async move { while rx.recv().await.is_some() {} });
            app.manage(BackendState {
                config: BackendConfig {
                    base_url: format!("http://127.0.0.1:{port}"),
                    token,
                },
                child: Mutex::new(Some(child)),
            });
            Ok(())
        })
        .on_window_event(|window, event| {
            if matches!(event, tauri::WindowEvent::Destroyed) {
                if let Some(state) = window.try_state::<BackendState>() {
                    if let Ok(mut guard) = state.child.lock() {
                        if let Some(child) = guard.take() {
                            let _ = child.kill();
                        }
                    }
                }
            }
        })
        .invoke_handler(tauri::generate_handler![backend_config])
        .run(tauri::generate_context!())
        .expect("error while running AgentSec Inspector");
}
