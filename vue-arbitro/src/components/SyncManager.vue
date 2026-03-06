<template>
  <div>
      <div style="margin-bottom: 20px; text-align: center;">
          <button v-if="!isDownloading" @click="pobierzDane" class="btn-main">
              🔄 Pobierz i zsynchronizuj dane
          </button>
          <p v-else style="color: #f39c12; margin-top: 10px; font-weight: bold;">
              ⏳ Trwa pobieranie... To może potrwać kilkanaście sekund.
          </p>
      </div>

      <div class="container sync-buttons-right">
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

const isDownloading = ref(false)
const isSyncing = ref(false)
const currentSync = ref(null)
const syncStatusMessage = ref('')
const syncStatusColor = ref('#7f8c8d')

const pobierzDane = async () => {
  isDownloading.value = true
  try {
      const response = await fetch('http://127.0.0.1:8000/api/pobierz_dane', { method: 'POST' })
      const result = await response.json()
      if (result.status === 'sukces') {
          emit('data-updated')
      } else {
          alert("Błąd: " + result.wiadomosc)
      }
  } catch (error) {
      alert("Błąd połączenia.")
  } finally {
      isDownloading.value = false
  }
}

const triggerSync = async (platform) => {
  isSyncing.value = true
  currentSync.value = platform
  syncStatusMessage.value = `Synchronizacja ${platform.toUpperCase()} w toku...`
  syncStatusColor.value = '#7f8c8d'

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
              syncStatusColor.value = '#2ecc71'
              
              emit('data-updated')
              
              setTimeout(() => syncStatusMessage.value = '', 4000)
          }
      }, 3000)
  } catch (error) {
      isSyncing.value = false
      syncStatusMessage.value = 'Błąd API.'
  }
}
</script>

<style scoped>
.sync-buttons-right { text-align: right; margin-bottom: 5px; display: flex; justify-content: flex-end; gap: 10px; }
.status-text { text-align: right; font-size: 0.85em; min-height: 20px; margin-top: 0; margin-bottom: 20px; }
.btn-main { background-color: #3498db; color: white; border: none; padding: 12px 20px; border-radius: 8px; font-weight: 800; cursor: pointer; text-transform: uppercase; box-shadow: 0 4px 10px rgba(52,152,219,0.3); }
.btn-pzpn { background-color: #e74c3c; color: white; border: none; padding: 12px 20px; border-radius: 8px; font-weight: 800; cursor: pointer; text-transform: uppercase; box-shadow: 0 4px 10px rgba(231,76,60,0.3); }
</style>