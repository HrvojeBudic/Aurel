#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

/// P2.10-C minimal Tauri desktop wrapper.
/// No native command bridge, file authority, secrets, or runtime control.
fn main() {
    tauri::Builder::default()
        .run(tauri::generate_context!())
        .expect("error while running Aurel Shell desktop wrapper");
}
