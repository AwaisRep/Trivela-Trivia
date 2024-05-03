<template>
  <div class="">

    <div v-if="isAuthenticated">
      
      <CardWrapper>

        <!-- Game cards to navigate to their relevant routes -->

        <GameCard @click="navigateTo('box2box')">
          <img :src="grid" class="icon" alt="Grid" />
          <h3>Box To Box</h3>
          <p>Click to view all Box To Box games!</p>
        </GameCard>


        <GameCard @click="navigateTo('GuessTheSide')">
          <img :src="formation" class="icon" alt="Formation" />
          <h3>Guess The Side</h3>
          <p>Click to view all Guess The Side games!</p>
        </GameCard>

        <GameCard @click="navigateTo('CareerPath')">
          <img :src="earth" class="icon" alt="Earth" />
          <h3>Career Path</h3>
          <p>Click to view all Career Path games!</p>
        </GameCard>

        <GameCard @click="navigateTo('trivia')">
          <img :src="quiz" class="icon" alt="Quiz" />
          <h3>Trivia</h3>
          <p>Click to find a worthy online opponent!</p>
        </GameCard>

      </CardWrapper>

    </div>
  </div>
</template>

<script lang="ts">
  import { defineComponent, computed } from 'vue';
  import { useRouter } from 'vue-router';
  import { useAuthStore } from "@/store/auth.ts";
  import grid from '@/assets/grid.svg';
  import formation from '@/assets/formation.svg';
  import earth from '@/assets/earth.svg';
  import quiz from '@/assets/quiz.svg';
  import GameCard from "@/components/Card.vue";
  import CardWrapper from "@/components/CardWrapper.vue";

  export default defineComponent({
    name: 'MainPage',
    components: {
      GameCard, CardWrapper
    },
    setup() {
      const router = useRouter();
      const authStore = useAuthStore();

      // Computed properties to reflect the current state from the store
      const isAuthenticated = computed(() => authStore.isAuthenticated);
      const title = "Main Page";

      // Method to navigate to different routes
      const navigateTo = (route: string) => {
        router.push(`/${route}`);
      };

      // Utilize the logout method from the auth store directly
      const logout = async () => {
        await authStore.logout();
        navigateTo('login'); // Redirect to login page or any other as needed
      };

      return {
        grid, formation, earth, quiz,
        title,
        isAuthenticated,
        logout,
        navigateTo
      };
    },
  });
</script>

<style scoped>

.icon {
  width: 50px;
  height: 50px;
}
</style>
