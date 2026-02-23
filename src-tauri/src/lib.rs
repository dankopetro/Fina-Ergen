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

fn get_python_exe(resource_dir: &std::path::Path) -> String {
    use std::process::Command;

    // 1. Prioridad: VENV del usuario en ~/.config/Fina/venv (persistente, siempre actualizado)
    let home = std::env::var("HOME").unwrap_or_else(|_| "/root".to_string());
    let xdg_config = std::env::var("XDG_CONFIG_HOME").unwrap_or_else(|_| format!("{}/.config", home));
    let user_venv = std::path::PathBuf::from(&xdg_config).join("Fina/venv/bin/python3");
    if user_venv.exists() {
        return user_venv.to_str().unwrap_or("python3").to_string();
    }
    
    // 2. Fallback: VENV dentro del AppImage (si se empaquetó uno)
    let venv_path = resource_dir.join("_up_/venv/bin/python3");
    let venv_dot_path = resource_dir.join("_up_/.venv/bin/python3");
    if venv_path.exists() {
        return venv_path.to_str().unwrap_or("python3").to_string();
    } else if venv_dot_path.exists() {
        return venv_dot_path.to_str().unwrap_or("python3").to_string();
    }
    
    // 3. Último recurso: Python del sistema
    if Command::new("python3").arg("--version").output().is_ok() {
        "python3".to_string()
    } else {
        "python".to_string()
    }
}

#[tauri::command]
fn scan_network_devices(app_handle: tauri::AppHandle) -> Result<String, String> {
    use std::process::Command;
    use tauri::Manager;

    // Obtener ruta real de recursos
    let resource_dir = app_handle.path().resource_dir()
        .map_err(|e| format!("No se pudo obtener resource_dir: {}", e))?;

    let python = get_python_exe(&resource_dir);

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
    let resource_dir = app_handle.path().resource_dir()
        .map_err(|e| format!("Error obteniendo ruta de recursos: {}", e))?;
    
    let python = get_python_exe(&resource_dir);
    let resource_path = resource_dir.join("plugins/doorbell/streamer.py");

    let _child = Command::new(python)
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
    
    let resource_dir = app_handle.path().resource_dir()
        .map_err(|e| format!("Error obteniendo ruta de recursos: {}", e))?;
    
    let python = get_python_exe(&resource_dir);
    let script_path = resource_dir.join("scripts/install_plugin.py");

    let output = Command::new(python)
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

#[tauri::command]
fn open_manual(app_handle: tauri::AppHandle) -> Result<(), String> {
    use tauri_plugin_opener::OpenerExt;
    use tauri::Manager;
    
    // Al estar fuera de src-tauri, se empaqueta en _up_/docs/
    let manual_path = app_handle.path().resource_dir()
        .map_err(|e| format!("Error en recursos: {}", e))?
        .join("_up_/docs/Manual_Guia_Configuracion_Fina.pdf");
        
    println!("[RUST] Intentando abrir manual en: {:?}", manual_path);
    
    if !manual_path.exists() {
        return Err(format!("Manual no encontrado en la ruta de instalación: {:?}", manual_path));
    }

    app_handle.opener().open_path(manual_path.to_str().unwrap(), None::<&str>)
        .map_err(|e| format!("No se pudo abrir el visor de PDF: {}", e))?;
    
    Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_shell::init())
        .invoke_handler(tauri::generate_handler![exit_app, hangup_doorbell, send_adb_command, start_streamer, execute_shell_command, spawn_shell_command, check_adb_status, execute_js_in_window, install_market_plugin, scan_network_devices, open_manual])
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::Destroyed = event {
                if window.label() == "main" {
                     println!("[RUST] Ventana principal cerrada. Matando zombies...");
                     kill_children();
                }
            }
        })
        .setup(|app| {
            use std::fs::create_dir_all;
            use std::path::PathBuf;

            // --- Preparamos Log para los procesos ocultos ---
            let config_dir = std::env::var("XDG_CONFIG_HOME")
                .map(PathBuf::from)
                .map(|p| p.join("Fina"))
                .unwrap_or_else(|_| {
                    std::env::var("HOME").map(PathBuf::from)
                        .unwrap_or_else(|_| PathBuf::from("/tmp"))
                        .join(".config/Fina")
                });
            let _ = create_dir_all(&config_dir);

            // --- LANZAR SIDECAR 'BRAIN' (Gestor Universal) ---
            // El Sidecar 'brain' se encarga de crear el venv, instalar dependencias,
            # [cfg(not(mobile))]
            {
                use tauri_plugin_shell::ShellExt;
                println!("[RUST] Lanzando Sidecar Universal 'brain'...");
                let sidecar = app.shell().sidecar("brain")
                    .map_err(|e| {
                        println!("[RUST] ❌ Error preparando sidecar: {}", e);
                        e
                    })?;
                
                let (mut _rx, _child) = sidecar.spawn()
                    .map_err(|e| {
                        println!("[RUST] ❌ Error al spawnear sidecar: {}", e);
                        e
                    })?;
                
                println!("[RUST] Sidecar brain iniciado exitosamente.");
            }

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
