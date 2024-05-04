<template>
  <main class="box">
    <section class="container pt-4">

      <nav class="navigation">
        <!-- Website logo -->
        <h1 class="logo" @click="toggleMenu">Trivela Trivia</h1>
        <img src="@/assets/dropdown.svg" @click="toggleMenu" alt="Trivela Trivia" class="icon logo-image">
        <div v-show="menuOpen" class="nav-items">
        <div class="spacer"></div>

        <!-- Spacer in layout-->
        <div class="spacer"></div>
        <div class="spacer"></div>

        <!-- Checks authentication and shows edit profile button when signed in--> 

        <router-link to="/" class="nav-button">Main Page</router-link>
        <router-link v-if="isAuthenticated" to="/edit-profile" class="nav-button">Edit Profile</router-link>

        <router-link to="/landing" v-if="isAuthenticated" @click="logout" class="nav-button">Logout</router-link>

        <button v-if="!isAuthenticated" class="nav-button" onclick="location.href='https://trivela-trivia.onrender.com/login'">Login</button>
        <button v-if="!isAuthenticated" class="nav-button" onclick="location.href='https://trivela-trivia.onrender.com/signup'">Sign Up</button>
        </div>
      </nav>

      <!-- Display current page content (router determines the page active) -->
      <RouterView class="flex-shrink-0" />

    </section>
    
    <!-- Sidebar to display user stats -->
    <aside v-if="isAuthenticated && userHistory" class="sidebar">
        <h2>User Stats</h2>
        <p><strong>Username:</strong> {{ userHistory["username"] }}</p>
        <p><strong>Matches Played:</strong> {{ userHistory["matches_played"] }}</p>
        <p><strong>Matches Won:</strong> {{ userHistory["matches_won"] }}</p>
        <p><strong>Matches Drawn:</strong> {{ userHistory["matches_drawn"] }}</p>
        <p><strong>Matches Lost:</strong> {{ userHistory["matches_lost"] }}</p>
        <p><strong>Total Points:</strong> {{ userHistory["user_points"] }}</p>
        <p><strong><router-link v-if="isAuthenticated" to="/leaderboard">Leaderboard</router-link></strong></p>
    </aside>
  </main>
</template>

<script lang="ts">
import { defineComponent, onMounted, computed, ref } from 'vue';
import { RouterView } from 'vue-router';
import { useAuthStore, UserHistory } from "@/store/auth.ts"; 

export default defineComponent({
  components: { RouterView },
  setup() {
    const authStore = useAuthStore();
    const menuOpen = ref(true);  // State to control the menu visibility

    // Check authentication when component is mounted
    onMounted(async () => {
      await authStore.checkAuthenticationStatus();
    });

    // Property to check if user is authenticated
    const isAuthenticated = computed(() => authStore.isAuthenticated);
    const userHistory = computed((): UserHistory => authStore.getHistory);

    // Method to logout
    const logout = async () => {
      if (authStore.isAuthenticated) {
        await authStore.logout();
      }
    };

    const toggleMenu = () => {
      menuOpen.value = !menuOpen.value;  // Toggle the menu visibility
    };

    return {
      isAuthenticated,
      logout,
      userHistory,
      menuOpen,
      toggleMenu
    };
  },
});
</script>

<style scoped>
  /* Custom fonts imported using the Google CDN */
  @import url('https://fonts.googleapis.com/css2?family=Open+Sans:wght@700&display=swap');
  @import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;700&display=swap');
  @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@700&display=swap');

  * {
      box-sizing: border-box;
  }

  ::-webkit-scrollbar {
    width: 20px;
  }

  body, html {
      margin: 0;
      padding: 0;
      font-family: 'Source Sans 3', sans-serif; /* Default font */
      overflow: auto;
  }

  h2, p {
    font-family: 'Source Sans 3', sans-serif;
  }

  .box {
    display: flex; /* Flexbox layout for ease */
  }

  .container { /* Main container for the page */
    display: flex;
    flex-direction: column;
    overflow: hidden;
    position: relative;
  }

  .navigation { /* Custom navbar styles */
      display: flex;
      justify-content: space-between; /* Create space between nav items */
      align-items: center;
      padding: 0 10px;
      background: transparent;
      position: sticky; /* Navbar sticks to the top of the page on scroll down */
      top: 0;
      z-index: 1000; /* Ensure the navbar is on top of other elements (Overriden in some pages). */
  }

  a, .navigation button {
    border: none;
    text-decoration: none; /* Remove underline from links */
  }

  .nav-button { /* Custom button styles */
    display: inline-block; /* Display buttons in a row */
    outline: none;
    cursor: pointer; /* Change cursor to pointer on hover */
    font-size: 14px;
    line-height: 1;
    transition-property: background-color,border-color,color,box-shadow,filter; /* Smooth transition on hover */
    transition-duration: .3s;
    letter-spacing: 2px;
    min-width: 160px;
    text-transform: uppercase;
    white-space: normal;
    font-weight: 700;
    text-align: center;
    padding: 16px 14px 18px;
    color: #616467;
    background-color: transparent;
    height: 48px;
  }

  .nav-button:hover {
      background-color: #505357;
      color: white
  }

  .logo { /* Logo styles */
    display: block;
    font-family: 'Montserrat', sans-serif;
    text-align: center;
    flex-grow: 1;
  }

  .spacer {
      flex-grow: 1;
  }

  .sidebar { /* Sidebar styles */
      background: #f8f9fa;
      padding: 20px;
      margin-top: 10px;
      border: 1px solid #ddd;
      border-radius: 4px;
      box-shadow: 0 2px 5px rgba(0,0,0,0.1);
      height: 23em; /* Responsive but fixed height for the sidebar */
      overflow: auto
  }

  .navigation .nav-items[style*="display: block"] {
    display: flex;
  }

  .icon { /* All svg icon styles have a fixed length */
      width: 50px;
      height: 50px;
    }

  .logo-image { /* A regular viewport should not display the menu logo icon */
    display: none;
  }

  /* Media queries */

  @media (min-width: 1200px) {
    .container {
        display: flex;
    }

    .RouterView {
        /* Ensure the main content takes most of the space */
        flex: 1;
        margin-right: 20px; /* Add some space before the sidebar */
    }

    .sidebar { /* The sidebar always sticks to the right on wide screens */
      position: relative;
      width: 15rem;
      margin-right: 10%;
      margin-top: 6rem;
    }
  }

  @media (max-width: 1200px) {

    .box { /* Column based layout for the main container when the viewport is too thin */
      flex-direction: column;
      justify-content: center;
      align-items: center;
    }

    .spacer { /* The spacer shortens when the viewport is too thin */
      flex-grow: 0;
    }

    .container { /* Gurantees the container is centered on thin viewports */
      align-items: center;
    }

    .sidebar { /* Sidebar half of the viewport and overlaps content on thinner viewports (Overriden on some pages). */
      flex-grow: 1000;
      max-width: 50%;
      margin-bottom: 1rem;
    }

    .content {
      order: 1;
    }
  }

  @media (max-width: 1000px) {
    .navigation {
      flex-direction: column; /* Stack the logo and the menu vertically on small screens */
    }

    .nav-items {
      display: flex;
      flex-direction: column;
      order: 2; /* Ensures nav-items list below the logo when displayed */
    }

    .logo {
      order: 1; /* Logo appears above the dropdown */
      display: none;
    }

    .logo-image { /* Logo image appears on small screens as the navbar */
      display: block;
      cursor: pointer;
    }

  }
</style>