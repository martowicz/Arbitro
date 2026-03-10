<template>
  <div>
    <SyncManager @data-updated="fetchMatches" />

    <div class="container">
        <div style="display: flex; gap: 30px; align-items: flex-start;">
            
            <div style="flex: 1;">
                <div v-if="totalPages > 1" class="pagination-controls">
                    <button 
                        @click="firstPage" 
                        :disabled="currentPage === 1"
                        class="page-btn"
                    >
                        Pierwsza
                    </button>
                    <button 
                        @click="prevPage" 
                        :disabled="currentPage === 1"
                        class="page-btn"
                    >
                        &laquo; Poprzednia
                    </button>
                    
                    <span class="page-info">Strona {{ currentPage }} z {{ totalPages }}</span>
                    
                    <button 
                        @click="nextPage" 
                        :disabled="currentPage === totalPages"
                        class="page-btn"
                    >
                        Następna &raquo;
                    </button>
                    <button 
                        @click="lastPage" 
                        :disabled="currentPage === totalPages"
                        class="page-btn"
                    >
                        Ostatnia
                    </button>
                </div>

                <p v-if="isLoadingMatches" style="text-align: center;">⏳ Ładowanie historii...</p>
                <p v-else-if="matches.length === 0" style="text-align: center;">Brak aktywności.</p>
                
                
                <div v-else>
                    <Activity 
                        v-for="match in paginatedMatches" 
                        :key="match.id || match.tytul + match.data" 
                        :activity="match" 
                    />
                </div>

                

            </div>

        </div> 
    </div>
  </div>
</template>

<script setup>
// ZMIANA: Importujemy 'computed' z vue
import { ref, computed, onMounted } from 'vue'
import SyncManager from './components/SyncManager.vue'
import AiCoach from './components/AiCoach.vue'
import Activity from './components/Activity.vue'

const matches = ref([])
const isLoadingMatches = ref(true)

// --- NOWE ZMIENNE DO PAGINACJI ---
const currentPage = ref(1)
const itemsPerPage = 10

// --- LOGIKA PAGINACJI (Magia Vue.js) ---

// 1. Liczymy ile jest w sumie stron (np. 25 meczów / 10 = 2.5 -> zaokrąglamy w górę do 3)
const totalPages = computed(() => {
    return Math.ceil(matches.value.length / itemsPerPage)
})

// 2. Wycinamy tylko te 10 meczów, które mają być na obecnej stronie
const paginatedMatches = computed(() => {
    const startIndex = (currentPage.value - 1) * itemsPerPage
    const endIndex = startIndex + itemsPerPage
    // Metoda slice(od, do) wycina kawałek tablicy
    return matches.value.slice(startIndex, endIndex)
})

// 3. Funkcje do klikania przycisków
const prevPage = () => {
    if (currentPage.value > 1) {
        currentPage.value--
        window.scrollTo({ top: 0, behavior: 'smooth' }) // Opcjonalnie: skroluje do góry po zmianie
    }
}

const firstPage = () => {
    if (currentPage.value > 1) {
        currentPage.value=1
        window.scrollTo({top: 0, behavior: 'smooth'})
    }
}

const lastPage = () => {
    if (currentPage.value < totalPages.value) {
        currentPage.value=totalPages.value
        window.scrollTo({top: 0, behavior: 'smooth'})
    }
}




const nextPage = () => {
    if (currentPage.value < totalPages.value) {
        currentPage.value++
        window.scrollTo({ top: 0, behavior: 'smooth' }) // Opcjonalnie: skroluje do góry po zmianie
    }
}
// ---------------------------------

const fetchMatches = async () => {
    isLoadingMatches.value = true
    try {
        const response = await fetch('http://127.0.0.1:8000/api/events')
        matches.value = await response.json()
        currentPage.value = 1 // ZMIANA: Po odświeżeniu danych wracamy na 1 stronę
    } catch (error) {
        console.error('Błąd pobierania danych:', error)
        matches.value = []
    } finally {
        isLoadingMatches.value = false
    }
}

onMounted(() => {
    fetchMatches()
})
</script>

<style scoped>
/* NOWE: Style dla przycisków paginacji */
.pagination-controls {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 20px;
    margin-top: 10px;
    padding-bottom: 10px;
}

.page-btn {
    padding: 8px 16px;
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-weight: bold;
    transition: background-color 0.2s;
}

.page-btn:hover:not(:disabled) {
    background-color: #0056b3;
}

.page-btn:disabled {
    background-color: #ccc;
    cursor: not-allowed;
}

.page-info {
    font-weight: 500;
    color: #555;
}
</style>