import { defineStore } from 'pinia';

// Define the user interface for strong typing
export interface User {
    username: string;
    matches_played: number;
    matches_won: number;
    matches_drawn: number;
    matches_lost: number;
    total_points: number;
    win_percentage: number;
}

// Define the leaderboard interface
export interface Leaderboard {
  leaderboardData: User[]; // Array of users
}

export const useLeaderboardStore = defineStore('leaderboard', {
  state: (): Leaderboard => ({ // Initialising state
    leaderboardData: []
  }),
  getters: {
    getLeaderboard: (state): User[] => state.leaderboardData // Getter to obtain leaderboard data
  },
  actions: {
    async fetchLeaderboard() {
      try {
        const response = await fetch(`https://trivela-trivia.onrender.com/leaderboard`, {
          method: 'GET',
          credentials: 'include' // Django user credentials
        });
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const data = await response.json();
        this.leaderboardData = data['leaderboard'];
      } catch (error) {
        console.error("Fetching leaderboard details failed:", error);
      }
    }
  }
});
