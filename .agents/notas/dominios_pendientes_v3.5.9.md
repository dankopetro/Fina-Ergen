# 📋 Dominios de Inteligencia - Fina Ergen v3.5.9

Este documento detalla los elementos que faltan integrar o expandir en los distintos "dominios" de Fina para alcanzar la cobertura total de una casa inteligente de última generación.

## 🔌 1. Dominio de Energía y Red (Networking & Power)
*   **Monitoreo Solar:** Integrar prefijos de Inversores Solares (Fronius, Enphase, SolarEdge, Victron Energy).
*   **Protección Eléctrica:** UPS Inteligentes (APC/Schneider, CyberPower, Eaton).
*   **Medidores de Consumo:** Shelly EM, Aeotec, Emporia Vue.

## 🧊 2. Dominio de Electrodomésticos (Smart Appliances)
*   **Línea Blanca (Expandir):** Hornos inteligentes (Bosch HomeConnect), Lavavajillas profesionales, Secadoras.
*   **Pequeños Electrodomésticos:** Cafeteras WiFi (Nespresso, DeLonghi, Jura), Tostadoras inteligentes.
*   **Cavas de Vino:** Monitoreo de temperatura para cavas inteligentes.

## 🌊 3. Dominio de Exteriores y Riego (Outdoor & Irrigation)
*   **Piscinas:** Controladores de pH (Blue Connect), Bombas de calor inteligentes (Zodiac), Robots limpiafondos (Dolphin).
*   **Sensores de Suelo:** Sensores de humedad para macetas y jardines (Xiaomi Flower Care).
*   **Estaciones Meteorológicas:** Netatmo, Ecowitt, Tempest.

## 🛋️ 4. Dominio de Confort y Aberturas (Comfort & Openings)
*   **Aberturas (Fase 2):** Garaje (Chamberlain, LiftMaster), Puertas automáticas, Sensores de ventana de alta sensibilidad.
*   **Calefacción:** Termostatos europeos y radiadores inteligentes (Netatmo, Eve Home).
*   **Fragancias:** Difusores de perfume WiFi (AromaTech, Rituals).

## 🏥 5. Dominio de Salud y Bienestar (Health & Wellness)
*   **Bio-monitoreo:** Balanzas inteligentes (Withings, Garmin), Monitores de sueño (Withings Sleep Analyzer).
*   **Purificación:** Filtros de aire (Dyson, Blueair, IKEA Starkvind).
*   **Fitness:** Integración con cintas de correr y bicicletas (Peloton, Technogym) para reporte de actividad.

## 🚗 6. Dominio de Movilidad (Mobility)
*   **Carga EV:** Cargadores de autos eléctricos (Tesla Wall Connector, Wallbox, JuiceBox).
*   **Vehículos:** Sincronización de estado de carga y clima del auto (Tesla, BMW ConnectedDrive, Mercedes me).

---
### 🛠️ Próximas Implementaciones en `network_scan.py`:
- [ ] Mapear prefijos de Inversores Solares (Huawei, Growatt).
- [ ] Agregar marcas de bio-monitoreo (Withings).
- [ ] Incluir fabricantes de cargadores EV.
