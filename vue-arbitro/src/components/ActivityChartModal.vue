<template>
  <div v-if="isOpen" class="modal-overlay" @click.self="closeModal">
    <div class="modal-content">
      
      <div class="modal-header">
        <h2>Heartrate and speed details</h2>
        <button @click="closeModal" class="close-btn">✖</button>
      </div>

      <div class="charts-wrapper" v-if="loaded">
        <div v-if="chartsData.length > 0">
          <div v-for="(item, index) in chartsData" :key="index" class="single-chart-block">
            <h3 class="chart-title">{{ item.title }}</h3>
            <div class="chart-container">
              <Line :data="item.chart" :options="chartOptions" />
            </div>
          </div>
        </div>
        <div v-else>
          <p style="text-align: center; color: red;">Brak danych do narysowania wykresu.</p>
        </div>
      </div>
      <div class="ai-summary-container" v-if="loaded">
        <div v-if="isAiLoading" class="ai-loading">
          <span class="spinner">🤖</span> Trener AI analizuje przebieg wysiłku. Proszę czekać...
        </div>
        <div v-else-if="aiSummaryText" class="ai-result">
          <h4>🧠 Analiza Trenera AI:</h4>
          <p>{{ aiSummaryText }}</p>
        </div>
        <div v-else-if="aiError" class="ai-error">
          <p>⚠️ Nie udało się pobrać analizy AI.</p>
        </div>
      </div>
      
      <div v-else class="loading-container">
        <p class="loading-text">⏳ Ładowanie danych z Garmina...</p>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler } from 'chart.js'
import { Line } from 'vue-chartjs'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)



const props = defineProps({
  isOpen: Boolean,
  itemId: [String, Number],
  itemType: String
})

const emit = defineEmits(['close'])

const loaded = ref(false)
const chartsData = ref([])

const chartOptions = ref({
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    heart_rate: {
      type: 'linear',
      position: 'left',
      min: 60,
      max: 200,
      title: { display: true, text: 'Tętno (bpm)', color: '#e74c3c' }
    },
    speed: {
      type: 'linear',
      position: 'right',
      min: 0,
      max: 40, 
      title: { display: true, text: 'Prędkość (km/h)', color: '#3498db' },
      grid: { drawOnChartArea: false }
    }
  },
  plugins: {
    legend: { display: true, position: 'top' },
    tooltip: { mode: 'index', intersect: false }
  }
})

const fetchChartData = async () => {
  loaded.value = false
  try {
    const endpoint = props.itemType === 'match' 
      ? `http://127.0.0.1:8000/api/matches/${props.itemId}/chart_data`
      : `http://127.0.0.1:8000/api/trainings/${props.itemId}/chart_data`

    const response = await fetch(endpoint)
    
    if (!response.ok) {
      const errorData = await response.json()
      alert(errorData.detail || "Nie udało się załadować danych.")
      emit('close')
      return
    }

    chartsData.value = await response.json()
    loaded.value = true
    
  } catch (error) {
    console.error("Błąd pobierania danych:", error)
    alert("Błąd połączenia z serwerem.")
    emit('close')
  }
}


const aiSummaryText = ref('')
const isAiLoading = ref(false)
const aiError = ref(false)

const fetchAiSummary = async () => {
  isAiLoading.value = true
  aiError.value = false
  aiSummaryText.value = ''

  try {
    const endpoint = `http://127.0.0.1:8000/api/analysis/${props.itemType}/${props.itemId}`
    const response = await fetch(endpoint)
    
    if (response.ok) {
      const data = await response.json()
      aiSummaryText.value = data.summary
    } else {
      aiError.value = true
    }
  } catch (error) {
    console.error("Błąd pobierania AI:", error)
    aiError.value = true
  } finally {
    isAiLoading.value = false
  }
}


watch(() => props.isOpen, (newVal) => {
  if (newVal === true) {
    fetchChartData()
    fetchAiSummary()
  } else {
    loaded.value = false
    chartsData.value = []
    aiSummaryText.value = ''
    aiError.value = false
  }
})

const closeModal = () => emit('close')
</script>

<style scoped>
.modal-overlay {
  position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
  background: rgba(0, 0, 0, 0.6); display: flex; justify-content: center; align-items: center;
  z-index: 1000; backdrop-filter: blur(4px);
}
.modal-content {
  background: #ffffff; width: 90%; max-width: 1500px; border-radius: 12px;
  padding: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.3);
}
.modal-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 15px; border-bottom: 2px solid #ecf0f1; padding-bottom: 10px;
}
.modal-header h2 { margin: 0; color: #2c3e50; }
.close-btn { background: none; border: none; font-size: 1.5em; cursor: pointer; color: #7f8c8d; }
.close-btn:hover { color: #e74c3c; }
.charts-wrapper { max-height: 70vh; overflow-y: auto; padding-right: 10px; }
.single-chart-block { margin-bottom: 30px; }
.chart-title { text-align: center; color: #34495e; margin-bottom: 10px; }
.chart-container { position: relative; height: 250px; width: 100%; }
.loading-container { height: 200px; display: flex; justify-content: center; align-items: center; }
.loading-text { font-size: 1.2em; color: #f39c12; font-weight: bold; }
.ai-summary-container { margin-top: 20px; padding: 15px; border-radius: 8px; background: #f8f9fa; border-left: 4px solid #3498db; }
.ai-loading { font-style: italic; color: #7f8c8d; display: flex; align-items: center; gap: 10px; }
.spinner { display: inline-block; animation: spin 2s infinite linear; font-size: 1.2em; }
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
.ai-result h4 { margin: 0 0 8px 0; color: #2c3e50; font-size: 1.1em; }
.ai-result p { margin: 0; color: #34495e; line-height: 1.5; font-size: 0.95em; white-space: pre-wrap; }
.ai-error { color: #e74c3c; font-size: 0.9em; }
</style>