import { defineStore } from 'pinia';

// Custom intergface that determines the state of the authentication
interface AuthState {
  isAuthenticated: boolean;
  email: string;
  userHistory: UserHistory;
}

// Custom interface that defines the user history
export interface UserHistory {
  username: String,
  matches_played: number,
  matches_won: number,
  matches_drawn: number,
  matches_lost: number,
  user_points: number,
}

// Defining the authentication store
export const useAuthStore = defineStore('auth', {
  // Initialising states
  state: (): AuthState => ({
    isAuthenticated: false, 
    email: '',
    userHistory: {username: "", matches_played: 0, matches_won: 0, matches_drawn: 0, matches_lost: 0, user_points: 0}, // Set the initial values
  }),
  getters: {
    getHistory: (state): UserHistory => { // Simple getter to obtain history in other pages
      return state.userHistory;
    }
  },
  actions: {
    // Function for obtaining the CSRF token required by django
    getCsrfToken() {
      const csrfTokenMatch = document.cookie.match(new RegExp('(^| )csrftoken=([^;]+)'));
      return csrfTokenMatch ? decodeURIComponent(csrfTokenMatch[2]) : '';
    },
    // Checking if the user is logged in using fetch
    async checkAuthenticationStatus() {
      try {
        const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/check_auth/`, {
          method: 'GET',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        if (response.ok) {
          const data = await response.json();
          this.isAuthenticated = data['authenticated'];
          this.email = data['user'].email;
          this.userHistory = data['history'];
        } else {
          console.error('Failed to check authentication status');
        }
      } catch (error) {
        console.error('Fetch error:', error);
      }
    },

    // Function for handling logout
    async logout() {
      const csrf_token = this.getCsrfToken();

      try {
        if (!csrf_token) { // Only process the logout is the CSRF token is set
          console.error('CSRF token is not available.');
          return;
        }

        const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/logout/`, {
          method: 'POST',
          credentials: 'include',
          headers: {
            Accept: "application/json",
            "Content-type": "application/json",
            "X-Csrftoken": csrf_token,
          },
        });

        if (response.ok) {
          this.isAuthenticated = false; // Set the authentication status to false on success
        } else {
          console.error('Failed to log out');
        }
      } catch (error) {
        console.error('Fetch error:', error);
      }
    },
  },
});
