<template>

  <div v-if="isAuthenticated">
    
    <CardWrapper>

      <!-- Generates a card for each career path game available in the database -->
      <GameCard v-for="game in careerPathData.games" :key="game.game_id" :item="game" @click="navigateTo('CareerPath/' + game.game_id)">
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
  import { useCareerPathStore } from "@/store/careerPath.ts";  // Import the Pinia store
  import GameCard from "@/components/Card.vue";
  import CardWrapper from "@/components/CardWrapper.vue";

  export default defineComponent({
    components: {
      GameCard, CardWrapper
    },
    setup() {
      const authStore = useAuthStore();
      const careerPathStore = useCareerPathStore(); // Use the career path store
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
        if (careerPathStore.games.length === 0) {
          careerPathStore.fetchGames();
        }
      });

      const isAuthenticated = computed(() => authStore.isAuthenticated); // Only authenticated users can fetch game details

      return {
        isAuthenticated,
        careerPathData: computed(() => ({ games: careerPathStore.games })),  // Provide a reactive reference to the games
        navigateTo
      };
    },

  })
</script>
