#!/bin/bash
# Suprimir warnings de GStreamer
export GST_DEBUG=0
export GST_PLUGIN_SCANNER=/bin/true

# Lanzar Fina
cd "." && npm run tauri dev
