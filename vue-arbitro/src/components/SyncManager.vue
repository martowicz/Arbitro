<template>
  <div>
      <div class="container sync-buttons-right">
          
          <button @click="triggerSync('all')" :disabled="isSyncing" class="btn-main" :class="{ 'disabled-btn': isSyncing }">
              {{ isSyncing && currentSync === 'all' ? '⌛ TRWA POBIERANIE...' : '🔄 Pobierz i zsynchronizuj wszystkie dane' }}
          </button>
          
          <button @click="triggerSync('pzpn')" :disabled="isSyncing" class="btn-pzpn" :class="{ 'disabled-btn': isSyncing }">
              {{ isSyncing && currentSync === 'pzpn' ? '⌛ TRWA...' : '⚽ Sync PZPN' }}
          </button>
          
          <button @click="triggerSync('garmin')" :disabled="isSyncing" class="btn-main" :class="{ 'disabled-btn': isSyncing }">
              {{ isSyncing && currentSync === 'garmin' ? '⌛ TRWA...' : '⌚ Sync Garmin' }}
          </button>
          
      </div>
      
      <p class="status-text" :style="{ color: syncStatusColor }">{{ syncStatusMessage }}</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const emit = defineEmits(['data-updated'])

const isSyncing = ref(false)
const currentSync = ref(null)
const syncStatusMessage = ref('')
const syncStatusColor = ref('#7f8c8d')

const triggerSync = async (platform) => {
  isSyncing.value = true
  currentSync.value = platform
  
  const nazwaDlaUzytkownika = platform === 'all' ? 'CAŁOŚCI' : platform.toUpperCase();
  syncStatusMessage.value = `Synchronizacja ${nazwaDlaUzytkownika} w toku. To może potrwać kilkanaście sekund...`
  syncStatusColor.value = '#f39c12' // Twój oryginalny pomarańczowy kolor ładowania

  try {
      await fetch(`http://127.0.0.1:8000/api/sync/${platform}`, { method: 'POST' })
      
      const checkInterval = setInterval(async () => {
          const statusRes = await fetch('http://127.0.0.1:8000/api/sync/status')
          const statusData = await statusRes.json()
          
          if (statusData.is_syncing === false) {
              clearInterval(checkInterval)
              isSyncing.value = false
              currentSync.value = null
              syncStatusMessage.value = '✅ Gotowe! Lista zaktualizowana.'
              syncStatusColor.value = '#2ecc71' // Zielony po sukcesie
              
              emit('data-updated')
              
              setTimeout(() => syncStatusMessage.value = '', 4000)
          }
      }, 3000)
  } catch (error) {
      isSyncing.value = false
      currentSync.value = null
      syncStatusMessage.value = '❌ Błąd połączenia z serwerem.'
      syncStatusColor.value = '#e74c3c'
  }
}
</script>

<style scoped>
/* Kontener: flex-wrap zapobiega ściskaniu przycisków na małych ekranach */
.sync-buttons-right { 
    display: flex; 
    justify-content: flex-end; 
    flex-wrap: wrap; /* Pozwala przyciskom spaść do nowej linii jeśli brakuje miejsca */
    gap: 15px; 
    margin-bottom: 5px; 
}

.status-text { 
    text-align: right; 
    font-size: 0.9em; 
    min-height: 20px; 
    margin-top: 5px; 
    margin-bottom: 10px; 
    font-weight: bold;
}

/* Główne przyciski z Twoimi kolorami */
.btn-main { 
    background-color: #3498db; 
    color: white; 
    border: none; 
    padding: 12px 20px; 
    border-radius: 8px; 
    font-weight: 800; 
    cursor: pointer; 
    text-transform: uppercase; 
    box-shadow: 0 4px 10px rgba(52,152,219,0.3); 
    transition: all 0.2s ease;
}

.btn-pzpn { 
    background-color: #e74c3c; 
    color: white; 
    border: none; 
    padding: 12px 20px; 
    border-radius: 8px; 
    font-weight: 800; 
    cursor: pointer; 
    text-transform: uppercase; 
    box-shadow: 0 4px 10px rgba(231,76,60,0.3); 
    transition: all 0.2s ease;
}

/* Efekty najechania myszką (tylko gdy przycisk nie jest zablokowany) */
.btn-main:hover:not(:disabled) {
    background-color: #2980b9;
    transform: translateY(-2px);
}

.btn-pzpn:hover:not(:disabled) {
    background-color: #c0392b;
    transform: translateY(-2px);
}

/* NOWE: Styl dla zablokowanych przycisków podczas synchronizacji */
.disabled-btn {
    background-color: #95a5a6 !important; /* Szary kolor ładowania */
    box-shadow: none !important;
    cursor: not-allowed;
    opacity: 0.7;
    transform: none !important;
}
</style>