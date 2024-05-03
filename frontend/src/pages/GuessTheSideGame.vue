<template>
    <div v-if="gameDetails">
      <h2 class="titleMessage">{{ gameDetails.message }}</h2>
  
      <GameWrapper>
        <div class="shrinkCard"> <!-- Overriding style so the two cards are displayed side by side (columns) -->
          <Card>
            <a><strong>Team: </strong>{{ gameDetails.teamName }}</a>
            <br>
            <a><strong>Description: </strong>{{ gameDetails.teamDescription }}</a>
            <br>
            <a><strong>Rules:</strong> The rules of this game are to successfully guess all the players in this starting eleven with just 15 guesses!</a>
          </Card>

          <Card>
            <div class="starting_xi">
              <h3><strong>The Starting XI</strong></h3>
              <!-- A list element is produced for every player in the starting eleven. Their positions are provided by default. The names are dependent on being guessed -->
              <ul>
              <li v-for="player in startingEleven" :key="player.position">
                  <strong>{{ player.position }}:</strong> {{ player.playerNames[0] || '' }}
              </li>
              </ul>
            </div>
          </Card>
        </div>

        <hr>

        <!-- Submission area only appears if the game is active -->
        <div class="userContent">
          <div class="formGroup" v-if="isFormGroupVisible">
          <input type="text" id="guess_input" v-model="guessInput" @keyup.enter="guess" placeholder="Enter your guess..."> <!-- Input field listens on the guess function-->
          <ButtonHero @click="guess">Submit</ButtonHero>
          </div>
          <p :key="gameDetails.guesses_left">Guesses remaining: {{ gameDetails.guesses_left }}</p>
        </div>

        </GameWrapper>
    </div>
  
    <div v-else>
      <p>Loading game details...</p>
    </div>
  
    <div id="toast"></div> <!-- Toast message container (can exist anywhere) -->
  </template>

<script lang="ts">
import { defineComponent, onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import { useFormationsStore } from "@/store/formation.ts";
import { useAuthStore } from '@/store/auth.ts';
import { useLeaderboardStore } from '@/store/leaderboard.ts';

import GameWrapper from '@/components/GameWrapper.vue';
import ButtonHero from '@/components/ButtonHero.vue';
import Card from '@/components/Card.vue';

// Custom interface for each player in the starting eleven
interface Player {
  position: string; // Their position e.g. GK
  playerNames: string[]; // All the names they're known by, e.g. ["Lionel Messi", "Messi"]
  guessed: boolean;
}

export default defineComponent({

    inheritAttrs:false,
    components: {
      GameWrapper, Card, ButtonHero
    },

    setup() {
        const route = useRoute(); // Vue router to pop game ID for fetching & guesses

        // Pinia stores that will be used
        const formationStore = useFormationsStore();
        const authStore = useAuthStore();
        const leaderboardStore = useLeaderboardStore();

        // Custom refs for reactive data, with custom type for gameDetails that holds all data about the game being played
        const gameDetails = ref<{ message: string; session_id: number; teamName: string; teamDescription: string, starting_eleven: string, guesses_left: number; game_over: boolean } | null>(null);
        const startingEleven = ref<Player[]>([]); // Holds the entire guessed team based on an array of the Player interface

        const guessInput = ref('');
        const isFormGroupVisible = ref(true);

        // Toast queue
        let toastQueue: { message: any; isError: any; }[] = [];
        let isToastShowing = false;

        // Fetch game details from the backend
        const fetchGameDetails = async () => {
            const gameID = route.path.split('/').pop() as string;
            const url = `https://localhost:8000/api/guess_the_side/game/${gameID}`;
            const csrfToken = document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1];

            const headers = new Headers({
                'Content-Type': 'application/json',
                ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {})
            });

            try {
                const response = await fetch(url, {
                    method: 'POST',
                    headers: headers,
                    credentials: 'include'
                });
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                const data = await response.json();
                gameDetails.value = data;
                handleFormVisibility(data);

                startingEleven.value = data.starting_eleven; // Set the starting eleven to the data fetched from the backend
                // We do this independently as it becomes messy when we try to constantly merge with gameDetails


            } catch (error) {
                console.error("Failed to fetch game details:", error);
            }
        };

        const guess = async () => {
            if (gameDetails.value !== null) {
                const gameID = gameDetails.value.session_id;
                const guessValue = guessInput.value;
                const url = `https://localhost:8000/api/guess_the_side/guess/${gameID}`;
                const csrfToken = document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1];

                const headers = new Headers({
                    'Content-Type': 'application/json',
                    ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {})
                });

                try {
                    const response = await fetch(url, {
                    method: 'POST',
                    headers: headers,
                    credentials: 'include', // A MUST FOR ALL DJANGO SESSIONS
                    body: JSON.stringify({ guess: guessValue })
                    });
                    if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                    }
                    const responseData = await response.json();

                    handleFormVisibility(responseData); //Gurantees the form data dissappears when the game is over
                    handleGuessResponse(responseData); //Custom toast message appears when a user makes their guess

                    gameDetails.value = { ...gameDetails.value, ...responseData, starting_eleven: gameDetails.value?.starting_eleven };  // Preserve clubs
                    if (gameDetails.value) {
                        gameDetails.value = { ...gameDetails.value, ...responseData }; // Merge the new data with the existing game details
                        startingEleven.value = responseData.guessed_players; // Get the new starting eleven if the user was able to guess correctly
                    } else {
                        throw new Error("Game details are not initialized.");
                    }
                } catch (error) {
                    console.error("Failed to send guess:", error);
                }
            }
            else {
                throw new Error("Invalid game error: No game details available.");
            }
        };

        function handleGuessResponse(response: { correct: string; }) { // Show toasts based on the response from the server
            if (response.correct === "yes") {
                showToast("Correct!", false);
            } else if (response.correct === "no") {
                showToast("Incorrect.", true);
            } else {
                // Handle case where response.correct is neither "yes" nor "no"
                showToast("Request could not be processed at this time.", null);
            }
        }
    
        function handleFormVisibility(response: { game_over: boolean; }) { // Hide form group if the game is over
            if (response.game_over) {
                isFormGroupVisible.value = false;
                // Fetch new data for the website, such as leaderboard, so the user doesn't need to refresh
                formationStore.fetchGames();
                authStore.checkAuthenticationStatus();
                leaderboardStore.fetchLeaderboard();
            }
        };

        // Show toast messages
        function showToast(message: string, isError: boolean | null) {
            toastQueue.push({ message, isError });

            if (!isToastShowing) {
                showNextToast();
            }
        }

        // Show the next toast message in the queue
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

              toast.className = "show";

              setTimeout(() => {
                  if (toast) {
                      toast.className = toast.className.replace("show", "");
                  }
                  isToastShowing = false;

                  if (toastQueue.length > 0) {
                      showNextToast();
                  }
              }, 3000);
            }
          }
        }

        onMounted(fetchGameDetails); // Fetch game details when the page loads

        return {
            gameDetails,
            guess,
            guessInput,
            startingEleven,
            isFormGroupVisible
        }
    },
})
</script>

<style scoped>
  .titleMessage {
    text-align: center;
    margin-top: 3rem;
  }


  hr { /* Line break size  */
    width: 100%;
  }

  /* Handles the styling for the submission styling such as input, submit btn and guesses remaining  */
  .userContent {
    width: 80%;
    margin-top: 1rem;
    display: flex;
    flex-direction: row; /* Gives the ability for elements to appear on the same line  */
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

  /* Toast styling */
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

   /* Style Overriders */
  /* The following styles are overriding shared components to cater the particular component to the game (guess the side) */
  h3 {
    font-size:larger;
  }

  .game-card {
    align-items: flex-start;
    border-radius: 1rem;;
    margin-left: 0;
  }

  .shrinkCard {
    display: flex;
    flex-direction: row;
    justify-content: space-around;
    justify-content: center;
  }

  /* These styles relate to the starting eleven data */
  .starting_xi { 
    position: relative;
    width: 100%;
  }

  .starting_xi h3 { /* Styling for the starting eleven header: 'The Starting XI' */
    display: block;
    position: relative;
    width: 100%;
    text-align: center;
  }

  /* The parent container that holds the three components are displayed one by one (not the two cards)  */
  .gameWrap {
    display: flex;
    flex-direction: column;
    margin-top: 5%;
    align-content: center;
    align-items: center;
    justify-content: center;
    max-width: fit-content;
  }
  /* Media queries */
  @media (max-width: 1000px) {
    .shrinkCard { /* Stacks the two cards one by one on thin viewports*/
      flex-direction: column;
      align-items: center;
      min-width: 300px;
      justify-content: center;
    }
  }

  @media (max-width: 775px) {
    .userContent { /* Stacks the form elements one by one on thin viewports */
      flex-direction: column;
      justify-content: center;
      align-items: center;
      justify-content: center;
    }

    .userContent p {
      margin-right: auto;
    }

    .formGroup {
      display: flex;
      flex-direction: column;
    }

    .game-card { /* Doesn't allow the cards to use the full width size on thin viewports */
      max-width: 90%;
    }
  }
</style>