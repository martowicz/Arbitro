<template>
  <div v-if="totalPages > 1" class="pagination-controls">
    <button 
      @click="$emit('changePage', 1)" 
      :disabled="currentPage === 1" 
      class="page-btn"
    >
      Pierwsza
    </button>
    
    <button 
      @click="$emit('changePage', currentPage - 1)" 
      :disabled="currentPage === 1" 
      class="page-btn"
    >
      &laquo; Poprzednia
    </button>
    
    <span class="page-info">Strona {{ currentPage }} z {{ totalPages }}</span>
    
    <button 
      @click="$emit('changePage', currentPage + 1)" 
      :disabled="currentPage === totalPages" 
      class="page-btn"
    >
      Następna &raquo;
    </button>
    
    <button 
      @click="$emit('changePage', totalPages)" 
      :disabled="currentPage === totalPages" 
      class="page-btn"
    >
      Ostatnia
    </button>
  </div>
</template>

<script setup>
// Definiujemy, jakich danych ten komponent oczekuje od rodzica
defineProps({
  currentPage: {
    type: Number,
    required: true
  },
  totalPages: {
    type: Number,
    required: true
  }
})

// Definiujemy, jakie zdarzenia ten komponent może wysłać do rodzica
defineEmits(['changePage'])
</script>

<style scoped>
/* Przeniesione z głównego pliku, żeby utrzymać porządek! */
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