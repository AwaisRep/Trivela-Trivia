import { createRouter, createWebHistory } from 'vue-router';

// Import all the pages that will be used in the frontend application
import MainPage from '@/pages/MainPage.vue';
import EditProfile from '@/pages/EditProfile.vue';
import Trivia from '@/pages/Trivia.vue';
import BoxToBox from '@/pages/BoxToBox.vue';
import BoxToBoxGame from '@/pages/BoxToBoxGame.vue';
import GuessTheSide from '@/pages/GuessTheSide.vue';
import GuessTheSideGame from '@/pages/GuessTheSideGame.vue';
import CareerPath from '@/pages/CareerPath.vue';
import CareerPathGame from '@/pages/CareerPathGame.vue';
import Leaderboard from '@/pages/Leaderboard.vue';
import Landing from '@/pages/Landing.vue';
import { useAuthStore } from "@/store/auth.ts";


const router = createRouter({
  history: createWebHistory(),
  routes: [ // All possible routes for the frontend application.: Login and Signup are handled by the backend.
    { path: '/', name: 'mainPage', component: MainPage, meta: { requiresAuth: true } },
    { path: '/edit-profile/', name: 'editProfile', component: EditProfile, meta: { requiresAuth: true } },
    { path: '/trivia/', name: 'trivia', component: Trivia, meta: { requiresAuth: true } },

    { path: '/box2box/', name: 'box2box', component: BoxToBox, meta: { requiresAuth: true } },
    { path: '/box2box/:gameID', name: 'box2box_game', component: BoxToBoxGame, meta: { requiresAuth: true } },

    { path: '/GuessTheSide/', name: 'guessTheSide', component: GuessTheSide, meta: { requiresAuth: true } },
    { path: '/GuessTheSide/:gameID', name: 'guessTheSide_game', component: GuessTheSideGame, meta: { requiresAuth: true } },

    { path: '/CareerPath/', name: 'careerPath', component: CareerPath, meta: { requiresAuth: true } },
    { path: '/CareerPath/:gameID', name: 'CareerPath_game', component: CareerPathGame, meta: { requiresAuth: true } },

    { path: '/leaderboard/', name: 'leaderboard', component: Leaderboard, meta: { requiresAuth: true } },

    {path: '/landing/', name: 'landing', component: Landing}
  ],
});

// This gurantees that the user is authenticated before accessing any route that requires authentication.
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore();
  // Check if the route requires authentication through the meta value
  if (to.matched.some(record => record.meta.requiresAuth)) {
    if (!authStore.isAuthenticated) {
      await authStore.checkAuthenticationStatus();
      if (!authStore.isAuthenticated) {
        // Redirect to the landing page if not authenticated
        return next({ path: '/landing/' });
      }
    }
  }
  next();
});

export default router;