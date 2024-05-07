<template>
    <div v-if="isVisible" class="popup-overlay">
        <div class="popup">
            <div class="popup-inner">
                <slot></slot> <!-- Allows content to be inserted -->
                <ButtonHero class="popup-close" @click="closePopup">Close Popup</ButtonHero>
            </div>
        </div>
    </div>
</template>

<script lang="ts">
  import { defineComponent } from 'vue';
  import ButtonHero from './ButtonHero.vue';

  export default defineComponent({
    components: {ButtonHero},
    props: { // Visiblity prop to determine if the popup is shown
      isVisible: Boolean
    },
    emits: ['update:isVisible'], // Emit an event to update the isVisible prop so the popup can be opened/closed
    setup(_props, { emit }) {
      const closePopup = () => { // Reverses the ability to see the popup when the close button is clicked
        emit('update:isVisible', false);
      };

      return { closePopup };
    }
  });
</script>

<style scoped>
  /* Popup is always in a fixed position to stack over any component */
  .popup {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center; /* Center the popup horizontally and vertically */
    align-items: center;
  }

  .popup-inner { /* Inner content of the popup */
    background: white;
    padding: 20px;
    border-radius: 10px;
    text-align: center; /* Center the button and title text in the popup */
  }

  .popup-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5); /* semi-transparent background */
    z-index: 1000; /* z-index refers to the stack level. 1000 means no component can overlap */
  }

  .popup-close { /* Close button for the popup */
    margin-top: 20px;
    padding: 10px 20px;
    cursor: pointer;
  }

  .sidebar {
      z-index: 99; /* Ensures the sidebar goes behind the popup overlay */
  }

  .navigation {
      z-index: 98; /* Ensures the navbar goes behind the popup overlay */
  }
</style>
