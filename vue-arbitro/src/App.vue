<template>
  <div>
    <SyncManager @data-updated="fetchActivities" />

    <div class="container">
        <div style="display: flex; gap: 30px; align-items: flex-start;">
            
            <div style="flex: 1;">
                <Pagination 
                :currentPage="currentPage" 
                :totalPages="totalPages" 
                @changePage="handlePageChange" 
                />

                <p v-if="isLoadingActivities" style="text-align: center;">⏳ Ładowanie historii...</p>
                <p v-else-if="activities.length === 0" style="text-align: center;">Brak aktywności.</p>
                
                <div v-else>
                    <div 
                        v-for="activity in paginatedActivities" 
                        :key="activity.id || activity.title + activity.date"
                        @click="handleActivityClick(activity)"
                        style="cursor: pointer;"
                    >
                        <Activity :activity="activity" />
                    </div>
                </div>
            </div>
        </div> 
    </div>
    
    <ActivityChartModal 
        :isOpen="isModalOpen" 
        :itemId="selectedItemId" 
        :itemType="selectedItemType"
        @close="isModalOpen = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import SyncManager from './components/SyncManager.vue'
import Activity from './components/Activity.vue'
import ActivityChartModal from './components/ActivityChartModal.vue'
import Pagination from './components/Pagination.vue'

// Zmienne do Modala
const isModalOpen = ref(false)
const selectedItemId = ref(null)
const selectedItemType = ref(null)

const openChart = (id, type) => {
  selectedItemId.value = id
  selectedItemType.value = type
  isModalOpen.value = true // TO OTWIERA MODAL!
}

// Obsługa kliknięcia w kafelek
const handleActivityClick = (activity) => {
    console.log("👉 Kliknięto aktywność:", activity)
    if (activity.match_id) {
        openChart(activity.match_id, 'match')
    } else if (activity.activity_id) {
        openChart(activity.activity_id, 'training')
    } else {
        alert("Brak przypisanego ID Garmina dla tej aktywności.")
    }
}

// Zmienne do listy i paginacji
const activities = ref([])
const isLoadingActivities = ref(true)
const currentPage = ref(1)
const itemsPerPage = 10

const totalPages = computed(() => Math.ceil(activities.value.length / itemsPerPage))

const paginatedActivities = computed(() => {
    const startIndex = (currentPage.value - 1) * itemsPerPage
    return activities.value.slice(startIndex, startIndex + itemsPerPage)
})

const handlePageChange = (newPage) => {
  currentPage.value = newPage
  window.scrollTo({ top: 0, behavior: 'smooth' }) // Gładki powrót na górę listy!
}
const fetchActivities = async () => {
    isLoadingActivities.value = true
    try {
        const response = await fetch('http://127.0.0.1:8000/api/events')
        activities.value = await response.json()
        currentPage.value = 1 
    } catch (error) {
        console.error('Błąd pobierania danych:', error)
        activities.value = []
    } finally {
        isLoadingActivities.value = false
    }
}

onMounted(() => {
    fetchActivities()
})
</script>

<style scoped>
.pagination-controls { display: flex; justify-content: center; align-items: center; gap: 20px; margin-top: 10px; padding-bottom: 10px; }
.page-btn { padding: 8px 16px; background-color: #007bff; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; transition: background-color 0.2s; }
.page-btn:hover:not(:disabled) { background-color: #0056b3; }
.page-btn:disabled { background-color: #ccc; cursor: not-allowed; }
.page-info { font-weight: 500; color: #555; }
</style>