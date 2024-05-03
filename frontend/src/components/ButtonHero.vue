<template>
    <button v-bind="$attrs"><slot></slot></button>
</template>

<style scoped>
    /* Custom button style that is globally used */
    button {
        display: inline-block;
        outline: none;
        cursor: pointer;
        font-size: 14px;
        line-height: 1;
        border-radius: 500px; /* Makes the button round */
        transition-property: background-color,border-color,color,box-shadow,filter; /* Adds a transition effect when the hover changes the properties */
        transition-duration: .3s;
        border: 1px solid transparent;
        letter-spacing: 2px;
        min-width: 160px;
        text-transform: uppercase;
        white-space: normal;
        font-weight: 700;
        text-align: center;
        padding: 16px 14px 18px; /* Gurantees the text has space inside the content area */
        color: #616467;
        box-shadow: inset 0 0 0 2px #616467; /* Adds a shadow border to the button */
        background-color: transparent;
        height: 48px;
    }

    button:hover { /* Gives a unique hover effect to change the colour of the button */ 
        color: #fff;
        background-color: #616467;
    }
</style>

<script>
    import { defineComponent } from 'vue';

    export default {
        name: 'ButtonHero',
    }
</script>