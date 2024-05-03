<template>

  <div v-if="isAuthenticated">
    
    <CardWrapper>

      <!-- Generates a card for each box2box game available in the database -->
      <GameCard v-for="game in boxToBoxData.games" :key="game.game_id" :item="game" @click="navigateTo('box2box/' + game.game_id)">
        <h4>Game ID: {{ game.game_id }}</h4>
        <h4>Status: {{ game.status }}</h4>
      </GameCard>
      <!-- Each card reads of the relevant ref component -->
      
    </CardWrapper>
  </div>

</template>


<script lang="ts">
  import { defineComponent, onBeforeMount, computed } from 'vue';
  import { useRouter } from 'vue-router';
  import { useAuthStore } from "@/store/auth.ts";
  import { useBoxToBoxStore } from "@/store/box2box";  // Import the Pinia store
  import GameCard from "@/components/Card.vue";
  import CardWrapper from "@/components/CardWrapper.vue";

  export default defineComponent({
    components: {
      GameCard, CardWrapper
    },
    setup() {
      const authStore = useAuthStore();
      const boxToBoxStore = useBoxToBoxStore(); // Use the box to box store
      const router = useRouter();
      
      // Custom function to navigate the particular game route
      const navigateTo = (route: string) => {
        router.push(`/${route}`);
      };

      // Fetch the games on before mount if not already loaded
      onBeforeMount(() => {
        if (!authStore.isAuthenticated) {
          authStore.checkAuthenticationStatus();
        }
        // Fetch games only if they have not been fetched yet
        if (boxToBoxStore.games.length === 0) {
          boxToBoxStore.fetchGames();
        }
      });

      const isAuthenticated = computed(() => authStore.isAuthenticated); // Only authenticated users can fetch game details

      return {
        isAuthenticated,
        boxToBoxData: computed(() => ({ games: boxToBoxStore.games })),  // Provide a reactive reference to the games
        navigateTo
      };
    },

  })
</script>
