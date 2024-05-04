<template>
  <div class="landing-page">
    <main class="main-content">
      <section class="hero-section">
        <h2>Welcome to your new home for football quizzes!</h2>
        <p>Click get started or the sign up button in order to get yourself registered instantly!</p>
        <ButtonHero class="get-started" onclick="location.href=`https://trivela-trivia.onrender.com/signup`">Get Started!</ButtonHero>
      </section>
    </main>
    <hr> <!-- Horizontal rule to separate the main content from the footer -->

    <!-- Footer section which presents our games that can be played -->
    <footer class="landing-footer">
      <div class="game">
          <img :src="grid" class="icon" alt="Grid" />
          <h3>Box To Box</h3>
          <p>Play a club-themed game where you attempt to guess players on a grid that play for a corresponding club!</p>
      </div>

      <div class="game">
          <img :src="formation" class="icon" alt="Formation" />
          <h3>Guess The Side</h3>
          <p>Attempt to guess the starting XI of historic footballing sides!</p>
      </div>

      <div class="game">
          <img :src="earth" class="icon" alt="Earth" />
          <h3>Career Path</h3>
          <p>Guess the player based on their career path and what they achieved!</p>
      </div>

      <div class="game">
          <img :src="quiz" class="icon" alt="Quiz" />
          <h3>Trivia</h3>
          <p>Play against an online opponent in a 60-second round 10 question match!</p>
      </div>
    </footer>
  </div>
</template>
  
<script lang="ts">
  import { defineComponent } from 'vue';
  import { useRouter } from 'vue-router';

  // Import all the necessary icons to use
  import grid from '@/assets/grid.svg';
  import formation from '@/assets/formation.svg';
  import earth from '@/assets/earth.svg';
  import quiz from '@/assets/quiz.svg';
  import ButtonHero from '@/components/ButtonHero.vue';

  export default defineComponent({
    name: 'MainPage',
    components: {
      ButtonHero
    },
    setup() {
      const router = useRouter();

      // Computed properties to reflect the current state from the store
      const title = "Landing Page";

      // Method to navigate to different routes
      const navigateTo = (route: any) => {
        router.push(`/${route}`);
      };

      return {
        title,
        navigateTo,
        grid,
        formation,
        earth,
        quiz,
      };
    },
  });
</script>
  
<style scoped>
  /* Import the Source Sans 3 font from Google Fonts CDN */
  @import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;700&display=swap');

  body {
      font-family: 'Source Sans 3', sans-serif;
  }

  h2, p {
      font-family: 'Source Sans 3', sans-serif;
  }

  h2 {
      font-weight: bold;
  }

  /* Main content with a flexbox column layout */
  .main-content {
      position: relative;
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      margin-top: 10rem;
  }

  /* Center the main area content */
  .main-content .hero-section {
      max-width: 50%;
      padding: 3rem;
  }

  .main-content .hero-section p, button {
      margin-top: 1rem;
  }


  /* The games shall not overlap into other components and they should begin at the start of their containers */
  footer {
    display: flex;
    max-width: 70%;
    align-items: flex-start;
    flex-wrap: wrap;
  }

  /* Each game shall be half of the width of the container to take up no more than two spots */
  .game {
    flex: 0 50%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    padding: 1rem;
  }

  .game img, h3, p {
    padding-top: 1rem;
  }

  /* All icons sizes must be 50px by 50px */
  .icon {
    width: 50px;
    height: 50px;
  }

  /* Media queries */
  @media (max-width: 700px) {

    /* Transform to a column based layout when the viewport is too thin */
    .main-content {
        position: relative;
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        margin-top: 1rem;
    }

    .main-content .hero-section {
        max-width: 100%;
    }

    .main-content .hero-section p, button {
        margin-top: 1rem;
    }

    /* Transform to a column based layout when the viewport is too thin */
    footer {
        max-width: 100%;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
  }
</style>
  