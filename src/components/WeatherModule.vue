<template>
    <div
        class="weather-module-container backdrop-blur-2xl bg-black/40 border border-white/5 rounded-[40px] p-8 flex flex-col justify-between overflow-hidden relative group transition-all duration-500 hover:border-cyan-500/30">

        <!-- Glow Effect -->
        <div
            class="absolute -top-20 -right-20 w-60 h-60 bg-cyan-500/10 rounded-full blur-[80px] group-hover:bg-cyan-500/20 transition-all duration-700">
        </div>
        <div
            class="absolute -bottom-20 -left-20 w-60 h-60 bg-purple-500/10 rounded-full blur-[80px] group-hover:bg-purple-500/20 transition-all duration-700">
        </div>

        <!-- Header: Location & Date -->
        <div class="flex items-start justify-between z-10">
            <div class="flex flex-col">
                <h2
                    class="text-2xl font-black text-white italic uppercase tracking-tighter drop-shadow-lg flex items-center gap-2">
                    <i class="fa-solid fa-location-dot text-cyan-500 text-sm animate-bounce"></i>
                    {{ cityName || 'Ubicación' }}
                </h2>
                <span class="text-[10px] font-bold text-slate-400 uppercase tracking-[0.3em] ml-1 mt-1">{{ currentDate
                }}</span>
            </div>
            <div class="px-3 py-1 bg-white/5 rounded-full border border-white/10 flex items-center gap-2">
                <i class="fa-solid fa-cloud text-cyan-300/70 text-[10px]"></i>
                <span class="text-[9px] font-black text-cyan-100 uppercase tracking-wider">LIVE</span>
            </div>
        </div>

        <!-- Main Content: Temp & Icon -->
        <div class="flex items-center justify-between mt-6 z-10 relative">
            <div class="flex flex-col">
                <div
                    class="flex items-start leading-none group-hover:scale-105 transition-transform duration-500 cursor-default">
                    <span
                        class="text-[6rem] font-black text-white tracking-tighter drop-shadow-[0_0_25px_rgba(255,255,255,0.1)] font-sans">
                        {{ Math.round(temperature) }}
                    </span>
                    <span class="text-4xl font-light text-cyan-500 mt-4 ml-1">°</span>
                </div>
                <span
                    class="text-lg font-bold text-cyan-100/80 uppercase tracking-widest mt-[-10px] ml-2 animate-in fade-in slide-in-from-left-4 duration-700">
                    {{ description }}
                </span>
            </div>

            <!-- Dynamic Weather Icon Container -->
            <div class="w-32 h-32 flex items-center justify-center relative">
                <!-- Sun/Moon Glow -->
                <div class="absolute inset-0 rounded-full blur-[30px] transition-all duration-1000"
                    :class="iconColorClass"></div>
                <i :class="[weatherIconClass, iconTextColorClass]"
                    class="text-7xl drop-shadow-2xl z-10 transform group-hover:rotate-12 transition-transform duration-500"></i>
            </div>
        </div>

        <!-- Details Grid -->
        <div class="grid grid-cols-3 gap-4 mt-8 pt-6 border-t border-white/5 z-10 relative">
            <!-- Humidity -->
            <div class="flex flex-col items-center gap-2 group/stat">
                <div
                    class="w-10 h-10 rounded-xl bg-cyan-900/20 border border-cyan-500/20 flex items-center justify-center shadow-inner group-hover/stat:bg-cyan-900/40 transition-colors">
                    <i class="fa-solid fa-droplet text-cyan-400"></i>
                </div>
                <div class="flex flex-col items-center">
                    <span class="text-lg font-black text-white leading-none">{{ humidity }}<span
                            class="text-[10px] align-top text-slate-400">%</span></span>
                    <span class="text-[8px] font-bold text-slate-500 uppercase tracking-widest mt-1">Humedad</span>
                </div>
            </div>

            <!-- Wind -->
            <div class="flex flex-col items-center gap-2 group/stat">
                <div
                    class="w-10 h-10 rounded-xl bg-slate-800/30 border border-white/10 flex items-center justify-center shadow-inner group-hover/stat:bg-slate-800/50 transition-colors">
                    <i class="fa-solid fa-wind text-slate-300"></i>
                </div>
                <div class="flex flex-col items-center">
                    <span class="text-lg font-black text-white leading-none">{{ windSpeed }}<span
                            class="text-[10px] align-top text-slate-400">km/h</span></span>
                    <span class="text-[8px] font-bold text-slate-500 uppercase tracking-widest mt-1">Viento</span>
                </div>
            </div>

            <!-- Feels Like -->
            <div class="flex flex-col items-center gap-2 group/stat">
                <div
                    class="w-10 h-10 rounded-xl bg-orange-900/20 border border-orange-500/20 flex items-center justify-center shadow-inner group-hover/stat:bg-orange-900/40 transition-colors">
                    <i class="fa-solid fa-temperature-half text-orange-400"></i>
                </div>
                <div class="flex flex-col items-center">
                    <span class="text-lg font-black text-white leading-none">{{ Math.round(feelsLike) }}°</span>
                    <span class="text-[8px] font-bold text-slate-500 uppercase tracking-widest mt-1">Sensación</span>
                </div>
            </div>
        </div>

        <!-- Forecast Footer -->
        <div class="mt-4 pt-4 border-t border-white/5 z-10">
            <div v-if="forecast && forecast.length > 0" class="grid grid-cols-3 gap-2">
                <div v-for="(day, idx) in forecastWithIcons" :key="idx"
                    class="flex flex-col items-center p-2 rounded-2xl hover:bg-white/5 transition-colors group/day">

                    <span class="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">{{ day.day
                    }}</span>

                    <i :class="day.iconClass"
                        class="text-xl mb-2 text-slate-200 group-hover/day:text-cyan-400 transition-colors"></i>

                    <div class="flex items-end gap-1 font-mono text-xs font-bold">
                        <span class="text-cyan-200">{{ day.min }}°</span>
                        <span class="text-slate-500">/</span>
                        <span class="text-white">{{ day.max }}°</span>
                    </div>
                </div>
            </div>
            <!-- Loading State or Empty -->
            <div v-else class="flex flex-col items-center justify-center h-24 gap-2 opacity-50">
                <i class="fa-solid fa-satellite-dish text-cyan-500 animate-pulse"></i>
                <span class="text-[9px] font-black uppercase tracking-widest text-slate-500">Cargando
                    Pronóstico...</span>
            </div>
        </div>
    </div>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
    temperature: { type: Number, default: 0 },
    humidity: { type: Number, default: 0 },
    windSpeed: { type: Number, default: 0 },
    feelsLike: { type: Number, default: 0 },
    description: { type: String, default: 'Despejado' },
    cityName: { type: String, default: 'Buenos Aires' },
    weatherCode: { type: Number, default: 800 },
    isDay: { type: Number, default: 1 },
    currentDate: { type: String, default: '' },
    forecast: { type: Array, default: () => [] }
});

const getIconClass = (code, day = true) => {
    if (code >= 200 && code < 300) return 'fa-solid fa-bolt';
    if (code >= 300 && code < 400) return 'fa-solid fa-cloud-rain';
    if (code >= 500 && code < 600) return 'fa-solid fa-cloud-showers-heavy';
    if (code >= 600 && code < 700) return 'fa-solid fa-snowflake';
    if (code >= 700 && code < 800) return 'fa-solid fa-smog';
    if (code === 800) return day ? 'fa-solid fa-sun' : 'fa-solid fa-moon';
    if (code > 800) return 'fa-solid fa-cloud';
    return 'fa-solid fa-cloud-sun';
};

const weatherIconClass = computed(() => getIconClass(props.weatherCode, props.isDay));

const forecastWithIcons = computed(() => {
    return props.forecast.map(f => ({
        ...f,
        iconClass: getIconClass(f.code, true) // Always use day icons for forecast
    }));
});

const iconColorClass = computed(() => {
    const code = props.weatherCode;
    if (code === 800) return props.isDay ? 'bg-orange-500/20' : 'bg-blue-500/20';
    if (code >= 200 && code < 300) return 'bg-yellow-500/20';
    if (code >= 500 && code < 600) return 'bg-cyan-500/20';
    return 'bg-slate-500/20';
});

const iconTextColorClass = computed(() => {
    const code = props.weatherCode;
    if (code === 800) return props.isDay ? 'text-orange-400' : 'text-blue-200';
    if (code >= 200 && code < 300) return 'text-yellow-400';
    if (code >= 500 && code < 600) return 'text-cyan-400';
    if (code >= 600 && code < 700) return 'text-white';
    return 'text-slate-200';
});
</script>

<style scoped>
.weather-module-container {
    width: 340px;
    height: auto;
    min-height: 520px;
}
</style>
