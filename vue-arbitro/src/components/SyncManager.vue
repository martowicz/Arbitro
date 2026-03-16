<template>
  <div>
      <div class="container sync-buttons-right">
          
          <button @click="toggleSettings" class="btn-settings">
              {{ showSettings ? '⬅️ ZAMKNIJ SEJF' : '⚙️ USTAWIENIA HASEŁ' }}
          </button>
          
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

      <div v-if="showSettings" class="settings-container">
        <h2>⚙️ Panel Konfiguracyjny</h2>
        <p class="subtitle">Twoje dane dostępowe są szyfrowane algorytmem AES i nigdy nie opuszczają tej maszyny.</p>

        <form @submit.prevent="saveSettings" class="settings-form">
          <div class="form-section">
            <h3>👤 Profil Sędziego</h3>
            <div class="form-group">
              <label>Imię i Nazwisko (do wyszukiwania w obsadach)</label>
              <div class="input-wrapper">
                <input v-model="form.surname_name" type="text" placeholder="np. Jan Kowalski" />
                <span v-if="status.has_surname_name" class="status-ok">✅ Skonfigurowano</span>
                <span v-else class="status-missing">❌ Brak danych</span>
              </div>
            </div>
          </div>

          <div class="form-section">
            <h3>⚽ Konto PZPN24</h3>
            <div class="form-group">
              <label>E-mail PZPN</label>
              <div class="input-wrapper">
                <input v-model="form.pzpn_email" type="email" placeholder="Zostaw puste, aby nie zmieniać" />
                <span v-if="status.has_pzpn_email" class="status-ok">✅ Skonfigurowano</span>
              </div>
            </div>
            <div class="form-group">
              <label>Hasło PZPN</label>
              <div class="input-wrapper">
                <input v-model="form.pzpn_password" type="password" placeholder="Zostaw puste, aby nie zmieniać" />
                <span v-if="status.has_pzpn_password" class="status-ok">✅ Skonfigurowano</span>
              </div>
            </div>
          </div>

          <div class="form-section">
            <h3>🏃 Garmin Connect</h3>
            <div class="form-group">
              <label>E-mail Garmin</label>
              <div class="input-wrapper">
                <input v-model="form.garmin_email" type="email" placeholder="Zostaw puste, aby nie zmieniać" />
                <span v-if="status.has_garmin_email" class="status-ok">✅ Skonfigurowano</span>
              </div>
            </div>
            <div class="form-group">
              <label>Hasło Garmin</label>
              <div class="input-wrapper">
                <input v-model="form.garmin_password" type="password" placeholder="Zostaw puste, aby nie zmieniać" />
                <span v-if="status.has_garmin_password" class="status-ok">✅ Skonfigurowano</span>
              </div>
            </div>
          </div>

          <div class="form-section">
            <h3>🤖 Sztuczna Inteligencja</h3>
            <div class="form-group">
              <label>Klucz API OpenAI</label>
              <div class="input-wrapper">
                <input v-model="form.openai_api_key" type="password" placeholder="sk-..." />
                <span v-if="status.has_openai" class="status-ok">✅ Skonfigurowano</span>
              </div>
            </div>
          </div>

          <div class="form-actions" style="display: flex; justify-content: flex-end; gap: 15px;">
            <button type="button" @click="toggleSettings" class="btn-cancel">
              ❌ Anuluj / Zamknij
            </button>
            
            <button type="submit" :disabled="isSaving" class="btn-settings">
              {{ isSaving ? '⏳ Szyfrowanie...' : '💾 Zapisz do sejfu' }}
            </button>
          </div>

          <p v-if="settingsMessage" :class="['message', isSettingsError ? 'message-error' : 'message-success']">
            {{ settingsMessage }}
          </p>
        </form>
      </div>

  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'

const emit = defineEmits(['data-updated'])

// --- LOGIKA SYNCHRONIZACJI ---
const isSyncing = ref(false)
const currentSync = ref(null)
const syncStatusMessage = ref('')
const syncStatusColor = ref('#7f8c8d')

const triggerSync = async (platform) => {
  isSyncing.value = true
  currentSync.value = platform
  
  const nazwaDlaUzytkownika = platform === 'all' ? 'CAŁOŚCI' : platform.toUpperCase();
  syncStatusMessage.value = `Synchronizacja ${nazwaDlaUzytkownika} w toku. To może potrwać kilkanaście sekund...`
  syncStatusColor.value = '#f39c12'

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
      currentSync.value = null
      syncStatusMessage.value = '❌ Błąd połączenia z serwerem.'
      syncStatusColor.value = '#e74c3c'
  }
}

// --- LOGIKA USTAWIEŃ (SEJFU) ---
const showSettings = ref(false)
const isSaving = ref(false)
const settingsMessage = ref('')
const isSettingsError = ref(false)

const form = reactive({
  surname_name: '',
  pzpn_email: '',
  pzpn_password: '',
  garmin_email: '',
  garmin_password: '',
  openai_api_key: ''
})

const status = reactive({
  has_surname_name: false,
  has_pzpn_email: false,
  has_pzpn_password: false,
  has_garmin_email: false,
  has_garmin_password: false,
  has_openai: false
})

const fetchStatus = async () => {
  try {
    const response = await fetch('http://127.0.0.1:8000/api/settings/status')
    const data = await response.json()
    Object.assign(status, data)
  } catch (error) {
    console.error("Błąd pobierania statusu sejfu:", error)
  }
}

// Otwieranie/zamykanie panelu
const toggleSettings = () => {
  showSettings.value = !showSettings.value
  if (showSettings.value) {
    fetchStatus() // Pobieramy status tylko gdy użytkownik rozwija panel
  }
}

const saveSettings = async () => {
  isSaving.value = true
  settingsMessage.value = ''
  isSettingsError.value = false

  const payload = {}
  for (const key in form) {
    if (form[key].trim() !== '') {
      payload[key] = form[key].trim()
    }
  }

  if (Object.keys(payload).length === 0) {
    settingsMessage.value = 'Nie wprowadzono żadnych zmian.'
    isSettingsError.value = true
    isSaving.value = false
    return
  }

  try {
    const response = await fetch('http://127.0.0.1:8000/api/settings/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })

    if (response.ok) {
      settingsMessage.value = '✅ Ustawienia zostały bezpiecznie zapisane!'
      Object.keys(form).forEach(key => form[key] = '')
      await fetchStatus() 
    } else {
      throw new Error('Błąd serwera')
    }
  } catch (error) {
    settingsMessage.value = '❌ Nie udało się zapisać ustawień.'
    isSettingsError.value = true
  } finally {
    isSaving.value = false
  }
}
</script>

<style scoped>
.sync-buttons-right { 
    display: flex; 
    justify-content: flex-end; 
    flex-wrap: wrap; 
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

/* Przyciski Główne */
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

.btn-main:hover:not(:disabled) {
    background-color: #2980b9;
    transform: translateY(-2px);
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

.btn-pzpn:hover:not(:disabled) {
    background-color: #c0392b;
    transform: translateY(-2px);
}

/* NOWY: Ciemnozielony przycisk ustawień */
.btn-settings { 
    background-color: #27ae60; 
    color: white; 
    border: none; 
    padding: 12px 20px; 
    border-radius: 8px; 
    font-weight: 800; 
    cursor: pointer; 
    text-transform: uppercase; 
    box-shadow: 0 4px 10px rgba(39, 174, 96, 0.3); 
    transition: all 0.2s ease;
}

.btn-settings:hover:not(:disabled) {
    background-color: #219a52;
    transform: translateY(-2px);
}

.btn-cancel {
  background-color: #ecf0f1;
  color: #7f8c8d;
  border: 1px solid #bdc3c7;
  padding: 12px 20px;
  border-radius: 8px;
  font-weight: bold;
  cursor: pointer;
  text-transform: uppercase;
  transition: all 0.2s ease;
}

.btn-cancel:hover {
  background-color: #bdc3c7;
  color: #2c3e50;
  transform: translateY(-2px);
}

.disabled-btn {
    background-color: #95a5a6 !important;
    box-shadow: none !important;
    cursor: not-allowed;
    opacity: 0.7;
    transform: none !important;
}

/* CSS dla rozsuwanego Panelu Ustawień */
.settings-container {
  margin-top: 15px;
  margin-bottom: 30px;
  padding: 25px;
  background: #fdfdfd;
  border-radius: 8px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.05);
  border: 1px solid #eee;
  text-align: left;
  color: #2c3e50;
  font-weight: 800; 
}

.settings-container h2 {
  margin-top: 0;
}

.subtitle {
  color: #7f8c8d;
  font-size: 0.9em;
  margin-bottom: 25px;
}

.form-section {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #f0f0f0;
}

.form-section h3 {
  margin-bottom: 12px;
  color: #2c3e50;
  font-size: 1.1em;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 600;
  font-size: 0.9em;
  color: #34495e;
}

.input-wrapper {
  display: flex;
  align-items: center;
  gap: 15px;
}

.input-wrapper input {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid #bdc3c7;
  border-radius: 6px;
  font-size: 1em;
}

.input-wrapper input:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 5px rgba(52,152,219,0.3);
}

.status-ok {
  color: #27ae60;
  font-size: 0.9em;
  font-weight: bold;
  white-space: nowrap;
}

.status-missing {
  color: #e74c3c;
  font-size: 0.9em;
  font-weight: bold;
  white-space: nowrap;
}

.form-actions {
  margin-top: 20px;
  text-align: right;
}

.message {
  margin-top: 15px;
  padding: 12px;
  border-radius: 6px;
  text-align: center;
  font-weight: bold;
}

.message-success {
  background: #d5f5e3;
  color: #27ae60;
}

.message-error {
  background: #fadbd8;
  color: #c0392b;
}
</style>