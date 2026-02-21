// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/


#[tauri::command]
fn kill_children() {
    use std::process::Command;
    println!("[RUST] Matando procesos hijos...");
    let _ = Command::new("pkill").args(&["-9", "-f", "weston --socket=wayland-1"]).output();
    let _ = Command::new("pkill").args(&["-9", "-f", "streamer.py"]).output();
    let _ = Command::new("pkill").args(&["-9", "-f", "monitor.py"]).output();
    let _ = Command::new("pkill").args(&["-9", "-f", "fina_api.py"]).output();
    let _ = Command::new("pkill").args(&["-9", "-f", "main.py"]).output(); 
    let _ = Command::new("pkill").args(&["-9", "-f", "mobile_hub.py"]).output();
    let _ = Command::new("pkill").args(&["-9", "-f", "network_scan.py"]).output();
    let _ = Command::new("pkill").args(&["-9", "-f", "monitor_ergen.py"]).output();
    let _ = Command::new("pkill").args(&["-9", "-f", "doorbell_final_app.py"]).output();
    let _ = Command::new("pkill").args(&["-9", "-f", "kdocker"]).output();
    let _ = Command::new("pkill").args(&["-9", "piper"]).output();
    let _ = Command::new("pkill").args(&["-9", "aplay"]).output();
    let _ = Command::new("waydroid").args(&["session", "stop"]).output();
}

#[tauri::command]
fn exit_app(app_handle: tauri::AppHandle) {
    println!("[RUST] Iniciando limpieza de salida (Comando)...");
    kill_children();
    println!("[RUST] Limpieza completada. Saliendo.");
    app_handle.exit(0);
}

#[tauri::command]
fn check_adb_status() -> Result<String, String> {
    use std::process::Command;
    println!("[RUST] Verificando estado de ADB...");
    let output = Command::new("adb")
        .args(&["devices"])
        .output()
        .map_err(|e| format!("Error verificando ADB: {}", e))?;
    let result = String::from_utf8_lossy(&output.stdout);
    println!("[RUST] ADB devices: {}", result);
    Ok(result.to_string())
}

#[tauri::command]
fn execute_shell_command(command: &str) -> Result<String, String> {
    use std::process::Command;
    let output = Command::new("sh")
        .env_remove("PYTHONHOME")
        .env_remove("PYTHONPATH")
        .arg("-c")
        .arg(command)
        .output()
        .map_err(|e| format!("Error ejecutando comando: {}", e))?;
    if !output.status.success() {
        return Err(format!("Command failed: {:?}", String::from_utf8_lossy(&output.stderr)));
    }
    let result = String::from_utf8_lossy(&output.stdout);
    Ok(result.to_string())
}

#[tauri::command]
fn scan_network_devices(app_handle: tauri::AppHandle) -> Result<String, String> {
    use std::process::Command;
    use tauri::Manager;

    // Buscar python3 disponible en el sistema
    let python = if Command::new("python3").arg("--version").output().is_ok() {
        "python3"
    } else {
        "python"
    };

    // Obtener ruta real del script desde los recursos empaquetados
    let resource_dir = app_handle.path().resource_dir()
        .map_err(|e| format!("No se pudo obtener resource_dir: {}", e))?;

    let script = resource_dir.join("_up_/iot/network_scan.py");

    if !script.exists() {
        return Err(format!("Script no encontrado: {:?}", script));
    }

    println!("[RUST] Escaneando red con: {:?}", script);

    let output = Command::new(python)
        .env_remove("PYTHONHOME")
        .env_remove("PYTHONPATH")
        .arg("-u")
        .arg(&script)
        .output()
        .map_err(|e| format!("Error al ejecutar network_scan.py: {}", e))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr);
        return Err(format!("network_scan.py error: {}", stderr));
    }

    let result = String::from_utf8_lossy(&output.stdout).to_string();
    println!("[RUST] Escaneo completado: {} bytes", result.len());
    Ok(result)
}


#[tauri::command]
fn spawn_shell_command(command: &str) -> Result<String, String> {
    use std::process::Command;
    println!("[RUST] Lanzando comando background: {}", command);
    Command::new("sh")
        .env_remove("PYTHONHOME")
        .env_remove("PYTHONPATH")
        .arg("-c")
        .arg(command)
        .spawn()
        .map_err(|e| format!("Error lanzando comando: {}", e))?;
    Ok("Launched successfully".to_string())
}

#[tauri::command]
fn start_streamer(app_handle: tauri::AppHandle) -> Result<String, String> {
    use std::process::Command;
    use tauri::Manager;
    println!("[RUST] Iniciando streamer desde frontend...");
    let check_output = Command::new("pgrep")
        .args(&["-f", "streamer.py"])
        .output()
        .map_err(|e| format!("Error verificando streamer: {}", e))?;
    if check_output.status.success() {
        return Ok("Streamer ya está corriendo".to_string());
    }
    
    // Obtener ruta dinámica de recursos
    let resource_path = app_handle.path().resource_dir()
        .map_err(|e| format!("Error obteniendo ruta de recursos: {}", e))?
        .join("plugins/doorbell/streamer.py");

    let _child = Command::new("python3")
        .env_remove("PYTHONHOME")
        .env_remove("PYTHONPATH")
        .arg(resource_path)
        .spawn()
        .map_err(|e| format!("Error iniciando streamer: {}", e))?;
    println!("[RUST] Streamer iniciado exitosamente");
    Ok("Streamer iniciado".to_string())
}

#[tauri::command]
fn send_adb_command(command: &str) -> Result<String, String> {
    use std::process::Command;
    println!("[RUST] Enviando comando ADB: {}", command);
    let output = Command::new("adb")
        .args(&["shell", command])
        .output()
        .map_err(|e| format!("Error ejecutando ADB: {}", e))?;
    if !output.status.success() {
        return Err(format!("ADB command failed: {:?}", String::from_utf8_lossy(&output.stderr)));
    }
    let result = String::from_utf8_lossy(&output.stdout);
    println!("[RUST] ADB output: {}", result);
    Ok(result.to_string())
}

#[tauri::command]
fn hangup_doorbell() -> Result<String, String> {
    use std::process::Command;
    let _ = Command::new("adb")
        .args(&["shell", "input", "tap", "225", "710"])
        .spawn(); 
    Ok("Timbre colgado".to_string())
}

#[tauri::command]
async fn execute_js_in_window(
    app_handle: tauri::AppHandle,
    window_label: &str,
    script: &str
) -> Result<String, String> {
    use tauri::Manager;
    
    println!("[RUST] Ejecutando JS en ventana: {}", window_label);
    
    // Obtener la ventana por su label
    let window = app_handle
        .get_webview_window(window_label)
        .ok_or_else(|| format!("Ventana '{}' no encontrada", window_label))?;
    
    // Ejecutar el script
    window
        .eval(script)
        .map_err(|e| format!("Error ejecutando script: {}", e))?;
    
    println!("[RUST] Script ejecutado exitosamente");
    Ok("Script executed".to_string())
}

#[tauri::command]
fn install_market_plugin(app_handle: tauri::AppHandle, category: &str, subpath: &str) -> Result<String, String> {
    use std::process::Command;
    use tauri::Manager;
    println!("[RUST] Instalando plugin de market: {}/{}", category, subpath);
    
    let script_path = app_handle.path().resource_dir()
        .map_err(|e| format!("Error obteniendo ruta de recursos: {}", e))?
        .join("scripts/install_plugin.py");

    let output = Command::new("python3")
        .env_remove("PYTHONHOME")
        .env_remove("PYTHONPATH")
        .args(&[script_path.to_str().unwrap(), category, subpath])
        .output()
        .map_err(|e| format!("Error ejecutando instalador: {}", e))?;
    
    let result = String::from_utf8_lossy(&output.stdout);
    if result.contains("ERROR") {
        return Err(result.to_string());
    }
    Ok(result.to_string())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![exit_app, hangup_doorbell, send_adb_command, start_streamer, execute_shell_command, spawn_shell_command, check_adb_status, execute_js_in_window, install_market_plugin, scan_network_devices])
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::Destroyed = event {
                if window.label() == "main" {
                     println!("[RUST] Ventana principal cerrada. Matando zombies...");
                     kill_children();
                }
            }
        })
        .setup(|app| {
            use tauri::Manager;
            use std::process::Command;

            let resource_dir = app.path().resource_dir()
                .expect("No se pudo obtener la carpeta de recursos");

            // Detectar python disponible en el sistema
            let python = if Command::new("python3").arg("--version").output().is_ok() {
                "python3"
            } else {
                "python"
            };

            // --- Arrancar fina_api.py (Backend REST) ---
            let api_script = resource_dir.join("_up_/fina_api.py");
            if api_script.exists() {
                println!("[RUST] Arrancando backend API: {:?}", api_script);
                let _ = Command::new(python)
                    .env_remove("PYTHONHOME")
                    .env_remove("PYTHONPATH")
                    .arg("-u")
                    .arg(&api_script)
                    .spawn();
            } else {
                println!("[RUST] ⚠ fina_api.py no encontrado en {:?}", api_script);
            }

            // --- Arrancar main.py (Cerebro) ---
            let brain_script = resource_dir.join("_up_/main.py");
            if brain_script.exists() {
                println!("[RUST] Arrancando cerebro: {:?}", brain_script);
                let _ = Command::new(python)
                    .env_remove("PYTHONHOME")
                    .env_remove("PYTHONPATH")
                    .arg("-u")
                    .arg(&brain_script)
                    .spawn();
            } else {
                println!("[RUST] ⚠ main.py no encontrado en {:?}", brain_script);
            }

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
