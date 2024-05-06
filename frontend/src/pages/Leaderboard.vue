<template>

    <div class="parent">
        <h2 class="titleMessage">Leaderboard Rankings:</h2>
        <div>
            <!-- We use the imported library EasyDataTable to format our leaderboard -->
            <EasyDataTable
                :headers="headers"
                :items="items"
            /> <!-- Header and item keys are referenced -->
        </div>
    </div>
</template>

<script lang="ts">
import { defineComponent, onMounted, ref} from 'vue';
import { useLeaderboardStore } from "@/store/leaderboard.ts"; 
import CardWrapper from '@/components/CardWrapper.vue';
import type { Header, Item } from "vue3-easy-data-table"; // Importing types from EasyDataTable

export default defineComponent({
    inheritAttrs: false,
    components: {CardWrapper},
    setup() {
        const leaderboardStore = useLeaderboardStore();

        // All the possible headers for the leaderboard table
        const headers: Header[] = [
            { text: "Username", value: "username" },
            { text: "Matches Played", value: "matches_played", sortable: true },
            { text: "Matches Won", value: "matches_won", sortable: true },
            { text: "Matches Lost", value: "matches_lost", sortable: true },
            { text: "Matches Drawn", value: "matches_drawn", sortable: true },
            { text: "Total Points", value: "total_points", sortable: true },
            { text: "Win Percentage", value: "win_percentage", sortable: true }
        ];

        const items = ref<Item[]>([]); // Array of items to be displayed in the leaderboard in a reactive way

        // Fetch leaderboard data when component is mounted
        onMounted(async () => {
            await leaderboardStore.fetchLeaderboard();
            const leaderboardData = leaderboardStore.getLeaderboard;
            if (Array.isArray(leaderboardData)) { // Check if the data is an array before we set the items (type check)
                    items.value = leaderboardData.map(user => ({
                        username: user.username,
                        matches_played: user.matches_played,
                        matches_won: user.matches_won,
                        matches_drawn: user.matches_drawn,
                        matches_lost: user.matches_lost,
                        total_points: user.total_points,
                        win_percentage: user.win_percentage
                    }));
                }
            });

        return {
            headers,
            items,
        };
    },
});
</script>

<style>

    /* Create a parent div so that it wraps the table and gurantees at least 280px of width */
    .parent {
        display: block;
        max-width: 100%;
        min-width: 280px;
        margin-top: 5%;
    }

    .titleMessage {
        padding: 1rem;
        text-align: center; /* Center the title */
    }
</style>