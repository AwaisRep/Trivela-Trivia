// stores/box2box.ts
import { defineStore } from 'pinia';

// Interface for game data
interface b2bGame {
  game_id: string;
  status: string;
}

// Interface for the state of the store
interface BoxToBoxData {
  games: b2bGame[]; // Array of games
}

export const useBoxToBoxStore = defineStore('box2box', {
  state: (): BoxToBoxData => ({
    games: [],
  }),
  actions: {
    async fetchGames() {
      this.games = []; // Reset games before fetching new ones
      try {
        const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/box2box/game`, {
          method: 'GET',
          credentials: 'include'
        });
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const data = await response.json();
        this.games = data.games as b2bGame[]; // Ensure the correct type is assigned
      } catch (error) {
        console.error("Fetching box to box games failed:", error);
      }
    }
  }
});
