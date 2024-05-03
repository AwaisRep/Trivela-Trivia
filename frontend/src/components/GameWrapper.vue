<template>
  <div class="gameWrap" v-bind="$attrs">
      <slot></slot>
  </div>
</template>

<style>
  /* Custom wrapper for all game content (override rules are implemented as each game is different) */
  .gameWrap {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    grid-gap: 10px;
    max-width: 90%; /* Don't fill the entire width available */
    margin-top: 10%;
    justify-content: space-around;
  }

  /* Media queries */
  @media (max-width: 1400px) {
    .gameWrap {  /* Adjust the number of columns to two on small screens. But this is overrided by many pages */
      grid-template-columns: 1fr 1fr;
    }
    }

    @media (max-width: 1100px) { /* Smallest screens will always abide by this rule */
    .gameWrap {
      grid-template-columns: 1fr;
    }
  } 

</style>

<script>
  import { defineComponent } from 'vue';

  export default { // Export the component to be used in pages
    name: 'GameWrapper',
  }
</script>