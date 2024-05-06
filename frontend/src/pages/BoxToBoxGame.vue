<template>
  <div v-if="gameDetails">
    <h2 class="titleMessage">{{ gameDetails.message }}</h2>

    <GameWrapper>
      <div class="grid">
        <!-- Top left cell -->
        <div class="grid-item">Clubs</div>
        <!-- Y-axis headers -->
        <div class="grid-item header" v-for="(yclub, yindex) in getYClubs" :key="'y' + yindex">
          {{ yclub }}
        </div>
        <!-- X-axis headers and grid data cells for each x-y combination -->
        <template v-for="(xclub, xindex) in getXClubs" :key="'x' + xindex">
          <div class="grid-item header">{{ xclub }}</div>
          <!-- Displaying cells for x against all y's -->
          <div class="grid-item" v-for="(yclub, yindex) in getYClubs" :key="'cell' + xindex + '_' + yindex">
            {{ isFormGroupVisible ? (gameDetails.grid['x' + (xindex + 1) + 'y' + (yindex + 1)] ? 'Guessed' : 'Not Guessed') + ' (' + yclub + ')' : 'Finished' }}
            <!-- We need to guarantee the game is active before we allow this group to display -->
          </div>
        </template>
      </div>

      <hr>

      <!-- Responsible for allowing the user to make guesses and view their progress -->
      <div class="userContent">
        <div class="formGroup" v-if="isFormGroupVisible"> <!-- Only show the form group if the game is active -->
          <input type="text" id="guess_input" v-model="guessInput" @keyup.enter="guess" placeholder="Enter your guess...">
          <ButtonHero @click="showPopup = true">Rules</ButtonHero>
        </div>
        <p :key="gameDetails.guesses_left">Guesses remaining: {{ gameDetails.guesses_left }}</p>
      </div>
    </GameWrapper>
  </div>

  <div v-else> <!-- If the game details are not loaded, display a loading message -->
    <p>Loading game details...</p>
  </div>

  <Popup :isVisible="showPopup" @update:isVisible="showPopup = $event">
            <div class="popup-content">
            <h4>Box To Box Rules</h4>
            <ul>
            <li>This game allows a maximum of 15 guesses</li>
            <li>Your job is to correctly guess 9 players who have played at both clubs at each intersection in x and y</li>
            <li>E.g. if Real Madrid was in x1 and Spain was in y1, a player to have represented both would be Sergio Ramos</li>
            <br>
            <li><strong>Note:</strong> Duplicate players as guesses are permitted</li>
            </ul>
            </div>
    </Popup>
  <div id="toast"></div> <!-- Toast message container (can exist anywhere) -->
</template>

<script lang="ts">
import { defineComponent, ref, onMounted, computed } from 'vue';
import { useRoute } from 'vue-router';
import { useBoxToBoxStore } from "@/store/box2box.ts";
import { useAuthStore } from '@/store/auth.ts';
import { useLeaderboardStore } from '@/store/leaderboard.ts';

import ButtonHero from '@/components/ButtonHero.vue';
import GameWrapper from '@/components/GameWrapper.vue';
import Popup from '@/components/Popup.vue';

// Custom grid interface for each club in the game (3x3)
interface ClubGrid {
x1: string;
x2: string;
x3: string;
y1: string;
y2: string;
y3: string;
}

// Custom grid state interface for each cell in the game (3x3)
interface GridState {
[key: string]: boolean; // Cell is either guessed or not
}

export default defineComponent({
  inheritAttrs:false,
  components: {
    GameWrapper,
    ButtonHero,
    Popup
  },
  setup() {
    const route = useRoute();
    
    // Relevant pinia stores
    const boxToBoxStore = useBoxToBoxStore();
    const authStore = useAuthStore();
    const leaderboardStore = useLeaderboardStore();

    // Toast variables
    let toastQueue: { message: any; isError: any; }[] = [];
    let isToastShowing = false;

    // Custom reactive variables for game details
    const gameDetails = ref<{ message: string; clubs: ClubGrid; grid: GridState; guesses_left: number; game_over: boolean } | null>(null);
    const clubs = ref<ClubGrid | null>(null); // Club grid is held seperately to represent the guessed tabs

    const guessInput = ref('');
    const isFormGroupVisible = ref(true);
    const showPopup = ref(false); // Rules popup

    // Two simple getter functions to map each boolean value to the 3x3 grid, represents which intersections have been guessed
    const getXClubs = computed(() => {
      return clubs.value ? [clubs.value.x1, clubs.value.x2, clubs.value.x3] : [];
    });

    const getYClubs = computed(() => {
      return clubs.value ? [clubs.value.y1, clubs.value.y2, clubs.value.y3] : [];
    });

    const fetchGameDetails = async () => {
      const gameID = route.path.split('/').pop() as string;
      const url = `https://trivela-trivia.onrender.com/box2box/game/${gameID}`;
      const csrfToken = document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1];
      console.log(url, gameID);
      const headers = new Headers({
        'Content-Type': 'application/json',
        ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {})
      });

      try {
        const response = await fetch(url, {
          method: 'POST',
          headers: headers,
          credentials: 'include' //MUST FOR DJANGO BACKEND
        });
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const data = await response.json();
        gameDetails.value = data; // All data changes with the response
        handleFormVisibility(data);

        if (!clubs.value) {  // Only set clubs if they haven't been set yet
          clubs.value = data.clubs;
        }
      } catch (error) {
        console.error("Failed to fetch game details:", error);
      }
    };

    const guess = async () => {
      const gameID = route.path.split('/').pop() as string;
      const guessValue = guessInput.value;
      const url = `https://trivela-trivia.onrender.com/box2box/guess/${gameID}`;
      const csrfToken = document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1];
  
      const headers = new Headers({
        'Content-Type': 'application/json',
        ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {})
      });

      try {
        const response = await fetch(url, {
          method: 'POST',
          headers: headers,
          credentials: 'include',
          body: JSON.stringify({ guess: guessValue })
        });
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const responseData = await response.json(); // Fetched data

        handleFormVisibility(responseData); //Gurantees the form data dissappears when the game is over
        handleGuessResponse(responseData); //Custom toast message appears when a user makes their guess

        gameDetails.value = { ...gameDetails.value, ...responseData, clubs: gameDetails.value?.clubs };  // Preserve clubs
      } catch (error) {
        console.error("Failed to send guess:", error);
      }
    };

    // Show toast function
    function showToast(message: string, isError: boolean | null) {
            toastQueue.push({ message, isError });

            if (!isToastShowing) {
                showNextToast();
            }
        }

    // Queue toast messages
    function showNextToast() {
      if (toastQueue.length > 0) {
        const { message, isError } = toastQueue.shift()!;
        const toast = document.getElementById("toast");

        if (toast) {
          isToastShowing = true;
          toast.textContent = message;

          if (isError === true) {
              toast.style.backgroundColor = "#d9534f";
          } else if (isError === false) {
              toast.style.backgroundColor = "#5cb85c";
          } else {
              toast.style.backgroundColor = "#808080";
          }

          toast.className = "show"; // Allow the toast to be displayed (Overrider of the CSS visibility property)

          setTimeout(() => {
              if (toast) {
                  toast.className = toast.className.replace("show", "");
              }
              isToastShowing = false;

              if (toastQueue.length > 0) {
                  showNextToast();
              }
          }, 3000); // 3 seconds appearance
        }
      }
    }

    // Handle the response from the guess request
    function handleGuessResponse(response: { correct: string; }) {
      if (response.correct === "yes") {
          showToast("Correct!", false);
      } else if (response.correct === "no") {
          showToast("Incorrect.", true);
      } else {
          // Handle case where response.correct is neither "yes" nor "no"
          showToast("Request could not be processed at this time.", null);
      }
    }
    
    // Handle the visibility of the form group based on the game state
    function handleFormVisibility(response: { game_over: boolean; }) {
      if (response.game_over) {
        isFormGroupVisible.value = false;  // Modify the `.value` property, not the ref itself (which is read-only)

        // Update the leaderboard, user history sidebar and fetch new game details to prevent a forced refresh
        boxToBoxStore.fetchGames();
        leaderboardStore.fetchLeaderboard();
        authStore.checkAuthenticationStatus();
      }
    };

    onMounted(fetchGameDetails); // Fetch game details on component mount

    return {
      gameDetails,
      getXClubs,
      getYClubs,
      guess,
      guessInput,
      isFormGroupVisible,
      showPopup
    };
  }
  });
</script>
  

  <style scoped>

  /* Custom styling for the 3x3 grid */
  .grid {
    display: grid;
    grid-template-columns: 150px repeat(3, 1fr); /* One column for x headers and three for y headers */
    grid-template-rows: 50px repeat(3, 1fr); /* One row for y headers and three for x clubs */
    text-align: center;
    grid-gap: 10px;
    max-width: 90%;
    overflow: auto;
  }
  
  .grid-item { /* Each item has centered text and custom styling */
    padding: 10px;
    border: 1px solid #ddd;
    display: flex;
    justify-content: center;
    align-items: center;
  }

  .titleMessage {
    text-align: center;
    margin-top: 3rem;
  }
  
  /* The parent container that holds the three components are displayed one by one (not the grid)  */
  .gameWrap {
    margin-top: 5%;
    align-items: center;
    max-width: 100%;
    grid-template-columns: 1fr;
    justify-items: center;
  }

  hr {
    width: 100%;
  }

  /* Handles the styling for the submission styling such as input, submit btn and guesses remaining  */
  .userContent {
    width: 80%;
    margin-top: 1rem;
    display: flex;
    flex-direction: row;
    align-items: center;
  }

  .userContent * {
    margin: 1rem; /* Spacing between elements  */
  }

  .userContent p {
    margin-left: auto;
  }

  input { /*  Custom input styling used across the site */
    outline: none;
    width: auto;
    border-top: hidden;
    float: left;
    padding: 8px;
    background: none;
  }

  ul {
    text-align: left;
  }

  /* Custom toast styling */
  #toast {
    visibility: hidden;
    min-width: 250px;
    margin-left: -125px;
    color: #fff;
    text-align: center;
    border-radius: 2px;
    padding: 16px;
    position: fixed;
    z-index: 1;
    left: 50%;
    bottom: 30px;
    font-size: 17px;
  }
  #toast.show {
      visibility: visible;
      -webkit-animation: fadein 0.5s, fadeout 0.5s 2.5s;
      animation: fadein 0.5s, fadeout 0.5s 2.5s;
  }

  /* Media queries for responsiveness */

  @media (max-width: 1000px) {
    .grid-item {
      padding: 5px;
      font-size: 12px; /* Smaller font size for table cells on small devices */
    }
  }

  @media (max-width: 775px) {
    .userContent { /* User submission section changes to column for smaller devices */
      flex-direction: column;
      justify-content: center;
      align-items: center;
    }

    .userContent p {
      margin-right: auto;
    }

    .formGroup {
      display: flex;
      flex-direction: column;
    }
  }
  </style>