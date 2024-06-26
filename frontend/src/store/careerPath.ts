// stores/car.ts
import { defineStore } from 'pinia';

// Interface for game data
interface careerPathGame {
  game_id: string;
  status: string;
}

// Interface for the state of the store
interface CareerPathData {
  games: careerPathGame[]; // Array of games
}

export const useCareerPathStore = defineStore('careerPath', {
  state: (): CareerPathData => ({ // Initialising state
    games: [],
  }),
  actions: {
    async fetchGames() {
      this.games = []; // Reset games before fetching new ones
      try {
        const response = await fetch(`https://trivela-trivia.onrender.com/career_path/game/`, {
          method: 'GET',
          credentials: 'include' // Django user credentials
        });
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const data = await response.json();
        this.games = data.games as careerPathGame[]; // Ensure the correct type is assigned
      } catch (error) {
        console.error("Fetching career path games failed:", error);
      }
    }
  }
});
