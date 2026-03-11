<template>
  <div class="activity-card" :style="{ backgroundColor: styles.cardBg }">
      <div class="activity-header">
          <div>
              <div class="activity-title">{{ activity.tytul }}</div>
              <div class="activity-date">{{ activity.data }}</div>
          </div>
      </div>
      
      <div class="activity-stats">
          <div class="stat-item">
              <div class="stat-value">🏃 {{ activity.dystans ? parseFloat(activity.dystans).toFixed(2) + ' km' : 'Brak' }}</div>
              <div class="stat-label">Dystans</div>
          </div>
          <div class="stat-item">
              <div class="stat-value">❤️ {{ activity.tetno ? activity.tetno + ' bpm' : 'Brak' }}</div>
              <div class="stat-label">Śr. Tętno</div>
          </div>
          <div class="stat-item">
              <div class="stat-value">🔥 {{ activity.kalorie ? activity.kalorie + ' kcal' : 'Brak' }}</div>
              <div class="stat-label">Kalorie</div>
          </div>
          <div class="stat-item">
              <div class="stat-value">⏱️ {{ activity.time}}</div>
              <div class="stat-label">Czas</div>
          </div>
      </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { ref } from 'vue'

const props = defineProps({
  activity: Object
})

const styles = computed(() => {
  const typ = props.activity.typ_wpisu;
  if (typ === 'past_matches'){ 
    return {cardBg: 'var(--past-match-bg-color)',  
            badgeBg: 'var(--past-match-bg-color)', 
            badgeText: 'white' };
    }
  if (typ === 'upcoming_matches'){
    return {cardBg: 'var(--upcoming-match-bg-color)',  
            badgeBg: 'var(--upcoming-match-bg-color)', 
            badgeText: 'white' };
    }

  return {cardBg: 'var(--training-bg-color)', 
        badgeBg: 'var(--training-bg-color)', 
        badgeText: 'white' };
})

const selectedItemId = ref(null)
const selectedItemType = ref(null)

const openChart = (id, type) => {
  selectedItemId.value = id
  selectedItemType.value = type
  isModalOpen.value = true
}
</script>

<style scoped>
.activity-card {
  background: var(--matchcard-color);
  backdrop-filter: blur(10px); /* Efekt mrożonego szkła */
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 10px;
  border-radius: 16px; 
  margin-bottom: 20px;
  margin-top: 20px;
}
.activity-card:hover { transform: translateY(-3px); box-shadow: 0 8px 20px rgba(0,0,0,0.15); }
.activity-header { display: flex; justify-content: space-between; align-items: flex-start; padding-bottom: 15px; margin-bottom: 15px; }
.activity-title {
  font-size: 1.4em;           /* Nieco większy */
  font-weight: 800;           /* Bardziej masywny (Extra Bold) */
  color: #ffffff;
  letter-spacing: -0.5px;     /* Nowoczesny, "ciasny" wygląd nagłówka */
  line-height: 1.2;           /* Zmniejszenie odstępu między liniami, jeśli tytuł jest długi */
  text-shadow: 0 2px 4px rgba(0,0,0,0.2); /* Delikatny cień dla czytelności */
  margin-bottom: 4px;
}
.activity-date { color: #ffffff; font-size: 0.95em; font-weight: 500; }
.activity-stats { display: flex; justify-content: space-around; background-color: rgba(255, 255, 255, 0.6); padding: 18px; border-radius: 20px; border: 1px solid rgba(0,0,0,0.05); }
.stat-item { text-align: center; flex: 1; }
.stat-value { font-size: 1.5em; font-weight: 800; color: #2c3e50; }
.stat-label { font-size: 0.85em; color: #444; text-transform: uppercase; letter-spacing: 1.2px; font-weight: 600; margin-top: 3px; }
.role-badge { padding: 6px 12px; border-radius: 15px; font-size: 0.85em; font-weight: 700; white-space: nowrap; margin-left: 15px; border: 1px solid rgba(0,0,0,0.1); }
</style>