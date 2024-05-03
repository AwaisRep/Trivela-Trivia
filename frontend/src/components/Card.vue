<template>
    <div class="game-card" v-bind="$attrs">
        <slot></slot>
    </div>
</template>

<style>
    /* Base styles for the cards of each game */
    .game-card {
        display: flex;
        flex-direction: column; /* Card elements should be stacked */
        align-items: center;
        box-shadow: rgba(0, 0, 0, 0.24) 0px 3px 8px; /* Adds a unique shadow to the card which gives it a 3d feel */
        border: 0px solid;
        padding: 1rem;
        margin: 10px;
        flex: 0 0 50%;
        cursor: pointer; /* Changes the cursor to a pointer when hovering over the card. This will be overriden */
    }

    .game-card:hover {
        background: #C9CCD3;
        background-image: linear-gradient(-180deg, rgba(255,255,255,0.50) 0%, rgba(0,0,0,0.50) 100%);
        background-blend-mode: lighten;
        transition-property: background-color,border-color,color,box-shadow,filter;
        transition-duration: .3s;
    }

    /* Media queries */
    @media (max-width: 800px) {
        .game-card {
            flex-wrap: wrap; /* Allows the cards to wrap when the screen is too prevent overflows */
            overflow: auto; /* Adds a scrollbar if the card should overflow */
        }
    }
</style>

<script>
  import { defineComponent } from 'vue';
  
export default {
  name: 'GameCard',
}
</script>
