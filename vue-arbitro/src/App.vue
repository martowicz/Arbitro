<template>
  <div>
    <SyncManager @data-updated="fetchMatches" />

    <div class="container">
        

        <div style="display: flex; gap: 30px; align-items: flex-start;">
            
            <div style="flex: 1;">
                <p v-if="isLoadingMatches" style="text-align: center;">⏳ Ładowanie historii...</p>
                <p v-else-if="matches.length === 0" style="text-align: center;">Brak aktywności.</p>
                
                <div v-else>
                    <Activity 
                        v-for="match in matches" 
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
import { ref, onMounted } from 'vue'
import SyncManager from './components/SyncManager.vue'
import AiCoach from './components/AiCoach.vue'
import Activity from './components/Activity.vue'

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