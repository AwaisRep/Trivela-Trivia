<template>
  <div class="parent">
    <div class="wrapped" v-bind="$attrs">
        <slot></slot>
    </div>
  </div>
</template>

<style scoped>
  /* Base styles for the card wrapper used in the main page*/
  .parent {
    display: flex;
    justify-content: center;
    align-items: center;
    margin-top: 10%;
  }

  .wrapped {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(500px, 1fr)); /* This implements a two grid column, but no mare than 50% can be filled. In that case, a new row is produced*/
    gap: 20px;
    max-width: 90%;
    margin: auto;
    width: max-content;
  }

  /* Media queries */
  @media (max-width: 800px) {
    .wrapped {
      grid-template-columns: 1fr; /* Changes the grid to a single column when the screen is less than 800px */
    }
  }
</style>

<script>
  import { defineComponent } from 'vue';

  export default {
    name: 'CardWrapper',
  }
</script>