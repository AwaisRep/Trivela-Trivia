// stores/formation.ts
import { defineStore } from 'pinia';

// Interface for game data
interface gtsGame {
  game_id: string;
  status: string;
}

// Interface for the state of the store
interface formationsData {
  games: gtsGame[]; // Array of games
}

export const useFormationsStore = defineStore('formations', {
  state: (): formationsData => ({ // Initialising state
    games: [],
  }),
  actions: {
    async fetchGames() {
      this.games = []; // Reset games before fetching new ones
      try {
        const response = await fetch(`https://trivela-trivia.onrender.com/guess_the_side/game/`, {
          method: 'GET',
          credentials: 'include' // Django user credentials
        });
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const data = await response.json();
        this.games = data.games as gtsGame[]; // Ensure the correct type is assigned
      } catch (error) {
        console.error("Fetching guess the side games failed:", error);
      }
    }
  }
});
