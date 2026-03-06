<template>
  <div class="match-card" :style="{ backgroundColor: styles.cardBg, borderLeft: '6px solid ' + styles.borderLeft }">
      <div class="match-header" :style="{ borderBottom: '1px solid ' + styles.headerLine }">
          <div>
              <div class="match-title">{{ match.tytul }}</div>
              <div class="match-date">{{ match.data }}</div>
          </div>
          <span class="role-badge" :style="{ backgroundColor: styles.badgeBg, color: styles.badgeText }">
              {{ match.podtytul }}
          </span>
      </div>
      
      <div class="match-stats">
          <div class="stat-item">
              <div class="stat-value">🏃 {{ match.dystans ? parseFloat(match.dystans).toFixed(2) + ' km' : 'Brak' }}</div>
              <div class="stat-label">Dystans</div>
          </div>
          <div class="stat-item">
              <div class="stat-value">❤️ {{ match.tetno ? match.tetno + ' bpm' : 'Brak' }}</div>
              <div class="stat-label">Śr. Tętno</div>
          </div>
          <div class="stat-item">
              <div class="stat-value">🔥 {{ match.kalorie ? match.kalorie + ' kcal' : 'Brak' }}</div>
              <div class="stat-label">Kalorie</div>
          </div>
      </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  match: Object
})

const styles = computed(() => {
  const typ = props.match.typ_wpisu;
  if (typ === 'past_matches') return { cardBg: '#9BFF8C', borderLeft: '#2ecc71', headerLine: 'rgba(46, 204, 113, 0.3)', badgeBg: '#2ecc71', badgeText: 'white' };
  if (typ === 'upcoming_matches') return { cardBg: '#FF9D00', borderLeft: '#ED9700', headerLine: 'rgba(46, 204, 113, 0.3)', badgeBg: '#CF8900', badgeText: 'white' };
  return { cardBg: '#87D3FF', borderLeft: '#3498db', headerLine: 'rgba(52, 152, 219, 0.3)', badgeBg: '#3498db', badgeText: 'white' };
})
</script>

<style scoped>
.match-card { border-radius: 12px; padding: 25px; margin-bottom: 25px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); transition: transform 0.2s, box-shadow 0.2s; margin-top: 0; }
.match-card:hover { transform: translateY(-3px); box-shadow: 0 8px 20px rgba(0,0,0,0.15); }
.match-header { display: flex; justify-content: space-between; align-items: flex-start; padding-bottom: 15px; margin-bottom: 15px; }
.match-title { font-size: 1.3em; font-weight: bold; color: #1a252f; margin-bottom: 3px; }
.match-date { color: #555; font-size: 0.95em; font-weight: 500; }
.match-stats { display: flex; justify-content: space-around; background-color: rgba(255, 255, 255, 0.6); padding: 18px; border-radius: 10px; border: 1px solid rgba(0,0,0,0.05); }
.stat-item { text-align: center; flex: 1; }
.stat-value { font-size: 1.5em; font-weight: 800; color: #2c3e50; }
.stat-label { font-size: 0.85em; color: #444; text-transform: uppercase; letter-spacing: 1.2px; font-weight: 600; margin-top: 3px; }
.role-badge { padding: 6px 12px; border-radius: 15px; font-size: 0.85em; font-weight: 700; white-space: nowrap; margin-left: 15px; border: 1px solid rgba(0,0,0,0.1); }
</style>