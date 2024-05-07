<template>
    <div v-if="gameDetails">
        <h2 class="titleMessage">{{ gameDetails.message }}</h2>
  
        <GameWrapper>
            <div class="shrinkCard">
                <!-- A card is generated for each club available in the player's career path with all the following attributes: -->
                <Card v-for="(career) in careerPath"> 
                    <p><strong>Team:</strong> {{ career.team_name }}</p>
                    <p><strong>Appearances:</strong> {{ career.appearances }}</p>
                    <p><strong>Goals:</strong> {{ career.goals }}</p>
                    <p><strong>Assists:</strong> {{ career.assists }}</p>
                    <p><strong>Season:</strong> {{ career.season }}</p>
                    <p v-if="career.is_loan"><strong>*This was a Loan*</strong></p> <!-- If the player was on loan at this club, this message will appear-->
                </Card>
            </div>

            <hr>
            <div class="userContent">
                <div class="formGroup" v-if="isFormGroupVisible"> <!-- Form group is only visible if the game is active -->
                    <input type="text" id="guess_input" v-model="guessInput" @keyup.enter="guess" placeholder="Enter your guess...">
                    <ButtonHero @click="guess">Submit</ButtonHero>
                </div>
                <p :key="gameDetails.guesses_left">Guesses remaining: {{ gameDetails.guesses_left }}</p>
            </div>
        </GameWrapper>
    </div>
    <div v-else>
        <p>Loading game details... Please click the back button and re-enter the game if this takes too long</p>
    </div>

    <Popup :isVisible="showPopup" @update:isVisible="showPopup = $event">
            <div class="popup-content">
            <h4>Career Path Rules</h4>
            <ul>
            <li>This game allows a maximum of 5 guesses</li>
            <li>Your job is to correctly guess the player based on the career path they took (in chronological order)</li>
            <li>Loans are stated where necessary</li>
            <br>
            <li><strong>Note:</strong> One point can be earnt for winning this game!</li>
            </ul>
            </div>
    </Popup>
    <div id="toast"></div> <!-- Toast message container (can exist anywhere) -->
</template>

<script lang="ts">
import { defineComponent, onMounted, ref } from 'vue';
import { useRoute } from 'vue-router';
import { useCareerPathStore } from "@/store/careerPath.ts";
import { useAuthStore } from '@/store/auth.ts';
import { useLeaderboardStore } from '@/store/leaderboard.ts';

import GameWrapper from '@/components/GameWrapper.vue';
import ButtonHero from '@/components/ButtonHero.vue';
import Card from '@/components/Card.vue';
import Popup from '@/components/Popup.vue';

// Custom interface that will handle the data relevant for each club the player represented
interface club {
    team_name: string,
    appearances: number,
    goals: number,
    assists: number,
    is_loan: boolean,
    season: number
}

export default defineComponent({

    inheritAttrs:false,
    components: {
        GameWrapper, Card, ButtonHero, Popup
    },
    setup() {

        const route = useRoute(); // Route object from Vue Router is utilised to fetch the id of the game

        // Pinia stores required
        const careerPathStore = useCareerPathStore();
        const authStore = useAuthStore();
        const leaderboardStore = useLeaderboardStore();

        // Reactive variables to hold the details about the game - updates on each submission
        const gameDetails = ref<{ message: string; session_id: number; careerPath: string; guesses_left: number; game_over: boolean } | null>(null);
        const careerPath = ref<club[]>([]); // Each club is inherits the interface defined earlier

        const guessInput = ref(''); // Current guess input by the user
        const isFormGroupVisible = ref(true); // Visibility of the form group
        const showPopup = ref(false); // Rules popup


        // Toast queues to display messages to the user
        let toastQueue: { message: any; isError: any; }[] = [];
        let isToastShowing = false;

        // Fetch the details about the game such as clubs, guesses remaining etc using fetch asynchronously
        const fetchGameDetails = async () => {
            const gameID = route.path.split('/').pop() as string; // As previously mentioned we need route to pop the game id
            const url = `https://trivela-trivia.onrender.com/career_path/game/${gameID}`; // In development this is localhost
            const csrfToken = document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1];

            //CSRF token required for authorisation of session
            const headers = new Headers({
                'Content-Type': 'application/json',
                ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {})
            });

            // Basic trial and error handling for the fetch request
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
                if (data) { // If game data is available, reactively change the components
                    gameDetails.value = data;
                    careerPath.value = data.career_path;
                }
                handleFormVisibility(data); // Only allow form data to be visible if the game is to be played


            } catch (error) {
                console.error("Failed to fetch game details:", error);
            }
        };

        const guess = async () => {
            if (gameDetails.value !== null) {
                const gameID = gameDetails.value.session_id;
                const guessValue = guessInput.value;
                const url = `https://trivela-trivia.onrender.com/career_path/guess/${gameID}`;
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
                    const responseData = await response.json();

                    handleFormVisibility(responseData); //Gurantees the form data dissappears when the game is over
                    handleGuessResponse(responseData); //Custom toast message appears when a user makes their guess

                    gameDetails.value = { ...gameDetails.value, ...responseData, careerPath: gameDetails.value?.careerPath };  // Preserve clubs
                    if (gameDetails.value) {
                        gameDetails.value = { ...gameDetails.value, ...responseData };
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
                careerPathStore.fetchGames();
                leaderboardStore.fetchLeaderboard();
                authStore.checkAuthenticationStatus();
            }
        };

        function showToast(message: string, isError: boolean | null) { // Show the toast message to the user
            toastQueue.push({ message, isError });

            if (!isToastShowing) {
                showNextToast();
            }
        }

        function showNextToast() { // Using queues to display toasts...
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

        onMounted(fetchGameDetails); // On page load, fetch the game details before the component is rendered

        return {
            gameDetails,
            guess,
            guessInput,
            careerPath,
            isFormGroupVisible,
            showPopup
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

  ul {
    text-align: left; /* Aligns the text to the left (intended for popups) */
  }


  /* Style Overriders */
  /* The following styles are overriding shared components to cater the particular component to the game (career path) */
  .gameWrap {
    position: relative;
    margin-top: 5%;
    flex-direction: column;
    flex-wrap: nowrap;
    align-items: center;
    justify-items: center;
    max-width: 100%;
    grid-template-columns: 1fr; /* Only one component can be shown per row (not the actual grid for game data) */
  }

  h3 {
    font-size:larger;
  }

  .game-card { /* Custom card styling for each club in the player's career path */
    width: 15rem;
    align-items: flex-start;
    border-radius: 1rem;;
    margin-left: 0;
  }

  .shrinkCard { /* This is the parent wrapper for the game-card */
    overflow: auto;
    display: grid;
    grid-template-columns: 1fr 1fr 1fr; /* Three cards per row on a regular width */
    grid-gap: 10px; /* Spacing between cards */
    max-height: 30rem;
    scrollbar-width: thin; /* Shortens the scrollbar */
    scrollbar-color: blue;
    padding-left: 10px;
  }
  
  /* Media queries to reorganise components when the viewport is too thin */
  @media (max-width: 1000px) {

    .shrinkCard { /* When the viewport is too thin, only one club card can be shown per row */
        grid-template-columns: 1fr;
        place-items: center;
    }

  }

  @media (max-width: 775px) {
    .userContent { /* When the viewport is too thin, the form group and guesses remaining are stacked */
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