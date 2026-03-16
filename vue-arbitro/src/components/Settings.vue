<template>
  <div class="settings-container">
    <h2>⚙️ Panel Konfiguracyjny (Sejf)</h2>
    <p class="subtitle">
      Twoje dane dostępowe są szyfrowane algorytmem AES i nigdy nie opuszczają tej maszyny.
    </p>

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

      <div class="form-actions">
        <button type="submit" :disabled="isLoading" class="btn-save">
          {{ isLoading ? '⏳ Szyfrowanie i zapis...' : '💾 Zapisz do sejfu' }}
        </button>
      </div>

      <p v-if="message" :class="['message', isError ? 'message-error' : 'message-success']">
        {{ message }}
      </p>

    </form>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';

// Stan formularza (to, co wpisuje użytkownik)
const form = reactive({
  surname_name: '',
  pzpn_email: '',
  pzpn_password: '',
  garmin_email: '',
  garmin_password: '',
  openai_api_key: ''
});

// Stan z bazy danych (True/False - czy dane istnieją)
const status = reactive({
  has_surname_name: false,
  has_pzpn_email: false,
  has_pzpn_password: false,
  has_garmin_email: false,
  has_garmin_password: false,
  has_openai: false
});

const isLoading = ref(false);
const message = ref('');
const isError = ref(false);

// Funkcja pobierająca status konfiguracji przy wejściu na stronę
const fetchStatus = async () => {
  try {
    const response = await fetch('http://localhost:8000/api/settings/status');
    const data = await response.json();
    Object.assign(status, data);
  } catch (error) {
    console.error("Błąd pobierania statusu:", error);
  }
};

// Funkcja wysyłająca nowe hasła do API
const saveSettings = async () => {
  isLoading.value = true;
  message.value = '';
  isError.value = false;

  // Tworzymy obiekt tylko z wypełnionymi polami (żeby nie nadpisać haseł pustymi stringami!)
  const payload = {};
  for (const key in form) {
    if (form[key].trim() !== '') {
      payload[key] = form[key].trim();
    }
  }

  if (Object.keys(payload).length === 0) {
    message.value = 'Nie wprowadzono żadnych zmian.';
    isError.value = true;
    isLoading.value = false;
    return;
  }

  try {
    const response = await fetch('http://localhost:8000/api/settings/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (response.ok) {
      message.value = '✅ Ustawienia zostały bezpiecznie zapisane!';
      // Czyścimy formularz ze względów bezpieczeństwa
      Object.keys(form).forEach(key => form[key] = '');
      // Odświeżamy "ptaszki"
      await fetchStatus(); 
    } else {
      throw new Error('Błąd serwera podczas zapisu.');
    }
  } catch (error) {
    message.value = '❌ Nie udało się zapisać ustawień.';
    isError.value = true;
  } finally {
    isLoading.value = false;
  }
};

// Uruchamiamy pobieranie statusu od razu po załadowaniu komponentu
onMounted(() => {
  fetchStatus();
});
</script>

<style scoped>
.settings-container {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
  background: #fdfdfd;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.subtitle {
  color: #666;
  font-size: 0.9em;
  margin-bottom: 30px;
}

.form-section {
  margin-bottom: 25px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.form-section h3 {
  margin-bottom: 15px;
  color: #2c3e50;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 600;
  font-size: 0.9em;
}

.input-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
}

input {
  flex: 1;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.status-ok {
  color: #27ae60;
  font-size: 0.85em;
  white-space: nowrap;
}

.status-missing {
  color: #c0392b;
  font-size: 0.85em;
  white-space: nowrap;
}

.form-actions {
  margin-top: 20px;
  text-align: right;
}

.btn-save {
  padding: 10px 20px;
  background: #2980b9;
  color: white;
  border: none;
  border-radius: 4px;
  font-weight: bold;
  cursor: pointer;
}

.btn-save:disabled {
  background: #95a5a6;
  cursor: not-allowed;
}

.message {
  margin-top: 15px;
  padding: 10px;
  border-radius: 4px;
  text-align: center;
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