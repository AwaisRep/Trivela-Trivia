<template>

  <div v-if="isAuthenticated">
    
    <CardWrapper>

      <!-- Generates a card for each guess the side game available in the database -->
      <GameCard v-for="game in formationsData.games" :key="game.game_id" :item="game" @click="navigateTo('GuessTheSide/' + game.game_id)">
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
  import { useFormationsStore } from "@/store/formation.ts";  // Import the Pinia store
  import GameCard from "@/components/Card.vue";
  import CardWrapper from "@/components/CardWrapper.vue";

  export default defineComponent({
    components: {
      GameCard, CardWrapper
    },
    setup() {
      const authStore = useAuthStore();
      const formationsStore = useFormationsStore(); // Use the formations store
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
        if (formationsStore.games.length === 0) {
          formationsStore.fetchGames();
        }
      });

      const isAuthenticated = computed(() => authStore.isAuthenticated); // Only authenticated users can fetch game details

      return {
        isAuthenticated,
        formationsData: computed(() => ({ games: formationsStore.games })),  // Provide a reactive reference to the games
        navigateTo
      };
      },

    })
</script>
