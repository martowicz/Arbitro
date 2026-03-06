<template>
  <div style="position: sticky; top: 20px;">
      <button @click="triggerAI" :disabled="isAiLoading" class="btn-ai" :class="{ 'disabled-btn': isAiLoading }">
          {{ isAiLoading ? '🧠 MYŚLĘ...' : '🤖 Zapytaj Trenera' }}
      </button>

      <div v-if="showAiPanel" class="ai-panel">
          <h3>🤖 Twój AI Coach:</h3>
          <p v-html="aiResponseText"></p>
      </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const showAiPanel = ref(false)
const isAiLoading = ref(false)
const aiResponseText = ref('')

const triggerAI = async () => {
  isAiLoading.value = true
  showAiPanel.value = true
  aiResponseText.value = '<i>Analizuję Twoje ostatnie kilometry, tętno i obciążenie meczowe... ⏳</i>'

  try {
      const response = await fetch('http://127.0.0.1:8000/api/trener_ai')
      const data = await response.json()
      
      aiResponseText.value = data.porada
          .replace(/#/g, '')
          .replace(/\*\*(.*?)\*\*/g, '<strong style="color: #3498db;">$1</strong>')
          .replace(/\*(.*?)\*/g, '<em style="color: #e67e22;">$1</em>')
          .replace(/\n/g, '<br>')
  } catch (error) {
      aiResponseText.value = '<span style="color: #e74c3c;">Błąd komunikacji z trenerem AI. Upewnij się, że backend działa.</span>'
  } finally {
      isAiLoading.value = false
  }
}
</script>

<style scoped>
.btn-ai { background-color: #9b59b6; color: white; border: none; padding: 15px 20px; border-radius: 8px; font-weight: 800; cursor: pointer; text-transform: uppercase; box-shadow: 0 4px 10px rgba(155,89,182,0.3); margin-bottom: 20px; font-size: 1.1em; width: 100%; }
.ai-panel { background-color: #2c3e50; border-left: 6px solid #9b59b6; border-radius: 12px; padding: 20px; margin-bottom: 25px; color: white; box-shadow: 0 10px 20px rgba(0,0,0,0.2); }
.ai-panel h3 { margin-top: 0; color: #ecf0f1; font-weight: 800; }
.ai-panel p { line-height: 1.6; font-size: 1.05em; opacity: 0.9; }
</style>