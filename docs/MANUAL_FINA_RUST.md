# 📖 Manual de Desarrollo - Fina Rust

## 🚀 **Guía de Desarrollo y Solución de Problemas**

### 📋 **Índice**
1. [Configuración Inicial](#configuración-inicial)
2. [Ejecución en Modo Desarrollo](#ejecución-en-modo-desarrollo)
3. [Problemas Comunes y Soluciones](#problemas-comunes-y-soluciones)
4. [Arquitectura Frontend-Backend](#arquitectura-frontend-backend)
5. [Debugging y Logs](#debugging-y-logs)
6. [Comandos Útiles](#comandos-útiles)

---

## 🔧 **Configuración Inicial**

### **Requisitos Previos**
```bash
# Verificar instalación de Rust
rustc --version

# Instalar Tauri CLI (requerido para desarrollo)
cargo install tauri-cli

# Verificar instalación
cargo tauri --version
```

### **Estructura del Proyecto**
```
test/fina-rust/src-tauri/
├── src/
│   └── main.rs              # Backend Rust
├── Cargo.toml              # Dependencias Rust
├── tauri.conf.json         # Configuración Tauri
└── target/                 # Binarios compilados
```

---

## 🚀 **Ejecución en Modo Desarrollo**

### **Método 1: Manual**
```bash
cd ./test/fina-rust/src-tauri
cargo tauri dev
```

### **Método 2: Script Automático**
```bash
cd ./test
python launch_fina_rust.py
```

### **Qué observar durante ejecución**
- **Terminal Rust**: Logs del backend
- **Ventana aplicación**: Interfaz Fina
- **DevTools (F12)**: Logs del frontend

---

## 🐛 **Problemas Comunes y Soluciones**

### **❌ Error: `no such command: 'tauri'`**
**Causa**: Tauri CLI no instalado
**Solución**:
```bash
cargo install tauri-cli
```

### **❌ Error: `Property 'toggleWindowMode' was accessed during render but is not defined`**
**Causa**: Función no expuesta en Vue
**Solución**: Agregar al return del componente:
```javascript
return {
    // ... otras propiedades
    toggleWindowMode,  // <-- Agregar aquí
    // ... resto de propiedades
};
```

### **❌ Error: `address already in use`**
**Causa**: Puerto 18000 ya está en uso
**Solución**:
```bash
# Matar proceso en puerto 18000
sudo lsof -ti:18000 | xargs kill -9

# O cambiar puerto en configuración
```

### **❌ El botón no funciona pero F11 sí**
**Causa**: Comunicación frontend-backend incorrecta
**Solución**: Usar `invoke` en lugar de API directa:
```javascript
// ❌ Incorrecto
const { getCurrentWindow } = window.__TAURI__.window;

// ✅ Correcto
const { invoke } = window.__TAURI__.core;
await invoke('toggle_fullscreen');
```

---

## 🏗️ **Arquitectura Frontend-Backend**

### **Backend Rust (`main.rs`)**
```rust
#[tauri::command]
fn toggle_fullscreen(window: Window) -> Result<(), String> {
    // Lógica de pantalla completa
    match window.is_fullscreen() {
        Ok(is_fullscreen) => {
            let new_state = !is_fullscreen;
            window.set_fullscreen(new_state)
        }
    }
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![toggle_fullscreen, exit_app])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

### **Frontend JavaScript (`index.html`)**
```javascript
// Definición de función
const toggleWindowMode = async () => {
    if (window.__TAURI__) {
        const { invoke } = window.__TAURI__.core;
        await invoke('toggle_fullscreen');
    }
};

// Exposición en Vue
return {
    toggleWindowMode,  // <-- Requerido para template
    // ... otras propiedades
};

// Uso en template
<button @click="toggleWindowMode">MODO VENTANA (F11)</button>
```

---

## 🔍 **Debugging y Logs**

### **Logs de Backend Rust**
```rust
#[tauri::command]
fn toggle_fullscreen(window: Window) -> Result<(), String> {
    println!("toggle_fullscreen llamado");  // Log en terminal
    
    match window.is_fullscreen() {
        Ok(is_fullscreen) => {
            println!("Estado actual fullscreen: {}", is_fullscreen);
            // ... más lógica
        }
    }
}
```

### **Logs de Frontend JavaScript**
```javascript
const toggleWindowMode = async () => {
    console.log("toggleWindowMode llamado");  // Log en DevTools
    
    if (window.__TAURI__) {
        console.log("Usando Tauri API");
        const { invoke } = window.__TAURI__.core;
        console.log("Invocando toggle_fullscreen...");
        
        try {
            await invoke('toggle_fullscreen');
            console.log("toggle_fullscreen invocado exitosamente");
        } catch (e) {
            console.error("Fallo switch fullscreen Tauri:", e);
        }
    }
};
```

### **Herramientas de Debugging**
1. **Terminal Rust**: Ver logs del backend
2. **DevTools (F12)**: Ver logs del frontend
3. **Script de diagnóstico**: `python debug_fullscreen.py`

---

## ⚡ **Comandos Útiles**

### **Desarrollo**
```bash
# Ejecutar en modo desarrollo
cargo tauri dev

# Compilar para producción
cargo tauri build

# Limpiar build
cargo clean
```

### **Depuración**
```bash
# Ver procesos Tauri
pgrep -f fina-app

# Ver puertos en uso
lsof -i :18000

# Logs detallados
RUST_LOG=debug cargo tauri dev
```

### **Python Scripts**
```bash
# Lanzar con logs
python launch_fina_rust.py

# Diagnosticar problemas
python debug_fullscreen.py
```

---

## 📝 **Mejores Prácticas**

### **1. Siempre agregar logs**
```rust
println!("Función llamada con parámetros: {:?}", params);
```

### **2. Manejo proper de errores**
```rust
match window.set_fullscreen(new_state) {
    Ok(_) => Ok(()),
    Err(e) => Err(format!("Failed to set fullscreen: {}", e))
}
```

### **3. Exponer funciones en Vue**
```javascript
return {
    functionName,  // <-- Siempre agregar aquí
};
```

### **4. Usar invoke para comunicación**
```javascript
const { invoke } = window.__TAURI__.core;
await invoke('command_name', { param: value });
```

---

## 🎯 **Caso de Estudio: Fix Pantalla Completa**

### **Problema**
- F11 funcionaba pero el botón no
- Error Vue de propiedad no definida

### **Solución Paso a Paso**
1. **Instalar Tauri CLI**: `cargo install tauri-cli`
2. **Agregar logs** en backend y frontend
3. **Corregir comunicación**: Usar `invoke`
4. **Exponer función** en Vue return
5. **Probar ambos métodos** (F11 y botón)

### **Resultado**
- ✅ F11 funciona
- ✅ Botón funciona
- ✅ Sin errores
- ✅ Logs funcionales

---

## 📚 **Recursos Adicionales**

### **Documentación Oficial**
- [Tauri Documentation](https://tauri.app/v1/guides/)
- [Rust Book](https://doc.rust-lang.org/book/)
- [Vue 3 Guide](https://vuejs.org/guide/)

### **Scripts Útiles**
- `launch_fina_rust.py`: Lanzador con diagnóstico
- `debug_fullscreen.py`: Herramienta de diagnóstico

---

## 🔄 **Flujo de Trabajo Recomendado**

1. **Configurar entorno**: Instalar Rust y Tauri CLI
2. **Ejecutar desarrollo**: `cargo tauri dev`
3. **Abrir DevTools**: F12 para debugging
4. **Probar cambios**: Recargar automáticamente
5. **Ver logs**: Terminal + DevTools
6. **Construir**: `cargo tauri build` para producción

---

**Última actualización**: 5 de Enero, 2026  
**Versión**: Fina Rust v0.1.0  
**Estado**: Fully Functional ✅
