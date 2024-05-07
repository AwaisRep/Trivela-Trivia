<template>
  <div v-if="isAuthenticated">
    <GameWrapper>

      <div class="onLoad" :style="{ display: showOnLoad ? 'block' : 'none' }">
        <h3 class="titleMessage">Welcome to Trivia!</h3>
        <ButtonHero @click="showPopup = true">Rules</ButtonHero>
        <Popup :isVisible="showPopup" @update:isVisible="showPopup = $event">
          <div class="popup-content">
          <h4>Trivia Rules</h4>
          <ul>
          <li>There are 60-seconds in this game. Each game has a maximum of 10 questions.</li>
          <li>You will be matched with another player actively searching the trivia game mode.</li>
          <li>The player with more correct answers at the end of the game will be declared winner and earn one point! A draw results in nothing!</li>
          <li>Winners earns two points, a draw earns one, and a loser earns none!</li>
          <br>
          <li><strong>Note:</strong> If no players are actively playing trivia, your matchmaking session will be cancelled.</li>
          </ul>
          </div>
        </Popup>
        <ButtonHero @click="connectToGame">Start Trivia Game</ButtonHero> <!-- Button to join the matchmaking queue -->
      </div>

      <!-- Game content appears only when the user can succesfully reach the matchmaking lobby -->
      <div class="gameSession" v-if="isConnected">
        <h3>{{ gameMessage }}</h3>
        <!-- Timer and question input -->
        <div class="questions">
          <p>Time left: {{ timeLeft }} seconds</p>
          <p>Question: {{ currentQuestion.question }}</p>
          <input v-model="userAnswer" @keyup.enter="submitAnswer" placeholder="Type your answer here..." />
          <ButtonHero @click="submitAnswer">Submit</ButtonHero>
        </div>
        <p>Question Number: {{ currentQuestion.index }} / 10</p>
        <p>Correct Answers: {{ correctAnswers }}</p>
      </div>
    </GameWrapper>

    <div id="toast"></div> <!-- Toast message container (can exist anywhere) -->
  </div>
</template>

<script lang="ts">
import { defineComponent, onMounted, onBeforeUnmount, computed, ref } from 'vue';
import { useAuthStore } from "@/store/auth.ts";
import { useLeaderboardStore } from "@/store/leaderboard.ts";

import GameWrapper from '@/components/GameWrapper.vue';
import ButtonHero from '@/components/ButtonHero.vue';
import Popup from '@/components/Popup.vue';

export default defineComponent({
  inheritAttrs: false,
  components: { GameWrapper, Popup, ButtonHero },
  setup() {
    // Pinia stores to use: One for authenticating users, the other to fetch leaderboard on game finish
    const authStore = useAuthStore();
    const leaderboardStore = useLeaderboardStore();

    const webSocket = ref<WebSocket | null>(null); // Socket for maintaining connection to session
    const isConnected = ref(false); // Displays the template if the user is connected
    const showPopup = ref(false); // Rules popup

    const gameMessage = ref(''); // Title message that updates
    const isAuthenticated = computed(() => authStore.isAuthenticated); // Check if user is authenticated

    const timeLeft = ref(60); // Starting time for the game - reactive component that ticks with socket
    const questionCount = ref(0); // Current question user is on
    const correctAnswers = ref(0);
    const currentQuestion = ref({ id: null, question: '', index: 0 }); // Custom interface to hold question data
    const userAnswer = ref('');

    const showOnLoad = ref(true);

    let toastQueue: { message: any; isError: any; }[] = [];
    let isToastShowing = false;

    // Function to manage WebSocket connection
    function setupWebSocket() {
      if (!webSocket.value || webSocket.value.readyState === WebSocket.CLOSED) { // Only proceed if websocket isn't active
        webSocket.value = new WebSocket(`wss://trivela-trivia.onrender.com/ws/matchmaking/`);
        webSocket.value.onopen = () => { // On open, set the connection status and display message
          isConnected.value = true;
          gameMessage.value = 'Connected! Waiting for an opponent...';
          showOnLoad.value = false;
        };

        webSocket.value.onmessage = (event) => { // Handles all incoming data from the socket
          const data = JSON.parse(event.data);
          if (data.gameStarted) {
            
            try {
              // Connect to the game session WebSocket URL provided by the server
              connectToGameSession(data.url);
            }

            catch {
              showToast("Could not connect to the game room", null);
              return;
            }

          }
          else {
            gameMessage.value = data.message;
          }
        };

        webSocket.value.onclose = () => {
          if (gameMessage.value === 'You have been removed from the queue due to inactivity.') {
            showToast("Unfortunately, no opponent could be found at this time. Try again later.", null);
          }
          isConnected.value = false;
          gameMessage.value = 'Disconnected. Check your connection and try again.';
        };

        webSocket.value.onerror = (error) => {
          console.error('WebSocket error: ', error);
          isConnected.value = false;
          gameMessage.value = 'Error connecting to the server. Please retry.';
        };
      }
    }

    function connectToGame() {
      setupWebSocket();
    }

    function connectToGameSession(gameUrl: string | URL) { // Handles socket for the game session
      if (webSocket.value) { // Close the existing WebSocket connection if open
        webSocket.value.close();
        isConnected.value = true; // Show form data now
      }

      // Open a new WebSocket connection for the game session
      webSocket.value = new WebSocket(`wss://trivela-trivia.onrender.com` + gameUrl);

      webSocket.value.onopen = () => {
        isConnected.value = true;
        gameMessage.value = 'Game has started!';
      };

      webSocket.value.onmessage = (event) => { // Handles incoming stream for the socket
        const data = JSON.parse(event.data);

        // The game is over
        if (data.game_over) {
          gameMessage.value = data.message;
          timeLeft.value = 0;
          authStore.checkAuthenticationStatus();
          leaderboardStore.fetchLeaderboard();
        }
        // Message is being received
        else if (data.message) {
          gameMessage.value = data.message;
        }
        // Check if a question is being received
        else if (data.question) {
          currentQuestion.value = {
            id: data.question_id,
            question: data.question,
            index: data.index
          };
        }
        // Remaining time is being received
        else if (data.remaining_time) {
          timeLeft.value = data.remaining_time;
        }
        // Answer result is being received
        else if (data.result) {
          handleGuessResponse(data.result);
          correctAnswers.value = data.correct_answers;
        }
      };

      //Error handling etc...
      webSocket.value.onclose = () => {
        isConnected.value = false;
        gameMessage.value = 'Disconnected. Check your connection and try again.';
      };

      webSocket.value.onerror = (error) => {
        console.error('WebSocket error: ', error);
        isConnected.value = false;
        gameMessage.value = 'Error connecting to the game session. Please retry.';
      };
    }

    // Function to handle submitting an answer and clearing the input field
    function submitAnswer() {
      if (webSocket.value && userAnswer.value) {
        webSocket.value.send(JSON.stringify({
          action: 'submit_answer',
          answer: userAnswer.value,
          question_id: currentQuestion.value.id
        }));
        userAnswer.value = ''; // Clear the input after sending
      }
    }

    // Creates the toast setup on each answer submission
    function handleGuessResponse(response: string ) {
      if (response === "correct") {
          showToast("Correct!", false);
      } else if (response === "incorrect") {
          showToast("Incorrect.", true);
      } else {
          // Handle case where response.correct is neither "yes" nor "no"
          showToast("Request could not be processed at this time.", null);
      }
    }

    // A queue is used to guranatee the promise of each toast
    function showToast(message: string, isError: boolean | null) {
      toastQueue.push({ message, isError });

      if (!isToastShowing) {
          showNextToast();
      }
    }

    // Show the next toast in the queue
    function showNextToast() {
      if (toastQueue.length > 0) {
        const { message, isError } = toastQueue.shift()!; // Move onto the next toast
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
          }, 3000); // Lasts for 3 seconds
        }
      }
    }

    onMounted(() => { // On page load check if user is authenticated
      if (!authStore.isAuthenticated) {
        authStore.checkAuthenticationStatus();
      }
    });

    onBeforeUnmount(() => { // Disconnect the socket when the user moves on to a new page/component
      if (webSocket.value) {
        webSocket.value.close();
      }
    });

    return {
      authStore,
      isAuthenticated,
      showPopup,
      isConnected,
      connectToGame,
      gameMessage,
      timeLeft,
      questionCount,
      correctAnswers,
      currentQuestion,
      userAnswer,
      submitAnswer,
      showToast,
      showOnLoad
    };
  },
})

</script>

<style scoped>
  /*  Wrapper for the game content */
  .gameWrap { 
      display: block;
      max-width: 100%;
      margin-top: 5%;
      text-align: center;
  }

  /* The title message which is reactive */
  .titleMessage {
      padding: 1rem;
      text-align: center;
  }

  ul {
    text-align: left;
  }

  /* Custom style for input fields */
  input {
      outline: none;
      width: auto;
      border-top: hidden;
      padding: 8px;
      background: none;
    }

  /* Toast styling */
  #toast {
      visibility: hidden; /* Only shown when activated in JS */
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
  #toast.show { /* Animation for fading the toast in and out */
      visibility: visible;
      -webkit-animation: fadein 0.5s, fadeout 0.5s 2.5s;
      animation: fadein 0.5s, fadeout 0.5s 2.5s;
  }

  .gameSession, .questions {
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .questions > * {
    margin: 1rem;
  }
</style>