<template>
  <div>
    <SyncManager @data-updated="fetchMatches" />

    <div class="container">
        <h1>🏆 Arbitro - Oś Czasu</h1>
        <p style="text-align: center; color: #555; margin-top: 0; margin-bottom: 40px;">
            Kompletna historia Twoich meczów i treningów
        </p>

        <div style="display: flex; gap: 30px; align-items: flex-start;">
            
            <div style="flex: 0 0 35%;">
                <AiCoach />
            </div>

            <div style="flex: 1;">
                <p v-if="isLoadingMatches" style="text-align: center;">⏳ Ładowanie historii...</p>
                <p v-else-if="matches.length === 0" style="text-align: center;">Brak aktywności.</p>
                
                <div v-else>
                    <MatchCard 
                        v-for="match in matches" 
                        :key="match.id || match.tytul + match.data" 
                        :match="match" 
                    />
                </div>
            </div>

        </div> 
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import SyncManager from './components/SyncManager.vue'
import AiCoach from './components/AiCoach.vue'
import MatchCard from './components/MatchCard.vue'

const matches = ref([])
const isLoadingMatches = ref(true)

const fetchMatches = async () => {
    isLoadingMatches.value = true
    try {
        const response = await fetch('http://127.0.0.1:8000/api/events')
        matches.value = await response.json()
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