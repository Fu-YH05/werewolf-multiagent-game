<template>
  <div id="app-root">
    <LoginView v-if="!isLoggedIn" @enter="handleEnter" />
    <App v-else />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import LoginView from './LoginView.vue'
import App from './App.vue'

const isLoggedIn = ref(false)

function handleEnter(apiKey) {
  if (apiKey) {
    localStorage.setItem('deepseek_api_key', apiKey)
  }
  isLoggedIn.value = true
}
</script>

<style>
#app-root {
  width: 100%;
  height: 100%;
}
</style>
