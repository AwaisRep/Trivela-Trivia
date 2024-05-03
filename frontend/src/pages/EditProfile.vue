<template>
<!-- Container for profile-->
  <div class="profile-container">
    <h1>{{ title }}</h1>
    <!-- form for changing profile -->
    <form class="profile-form" @submit.prevent="submitForm">

      <!-- field for updating profile -->
      <div class="form-group">
        <label for="id_email">Email</label> 
        <input type="email" name="Email" id="id_email" ref="email" :placeholder= 'authStore.email'>
      </div>

      <div class="form-group">
        <label for="id_pass1">New Password</label> 
        <input type="password" name="Password" id="id_pass1" ref="password1">
      </div>

      <div class="form-group">
        <label for="id_pass2">Confirm Password</label> 
        <input type="password" name="Password" id="id_pass2" ref="password2"> <!-- Corrected ref from 'password1' to 'password2' -->
      </div>

      <!-- submit button -->
      <button class="submit-button">Submit</button>
    </form>
    <!-- gives success or error message if submission is successul or unsuccessful -->
    <div v-if="submissionStatus === 'success'" class="success-message">
      Profile Successfully Updated!
    </div>
    <div v-else-if="submissionStatus === 'error'" class="error-message">
      {{ errorMessage }}
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, onMounted } from "vue";
import { useAuthStore } from "@/store/auth.ts";

export default defineComponent({
  setup() {
    // Intializing authentication store
    const authStore = useAuthStore();
    // Checking authentication when component is mounted
    onMounted(async () => {
      if (!authStore.isAuthenticated) {
        await authStore.checkAuthenticationStatus();
      }
    });

    return {
      authStore
    };
  },

  data() {
    return {
      submissionStatus: '',
      errorMessage: '',
      title: "Profile",
      change_counter: false, // Checks if any changes were made to the form
    };
  },

  methods: {
  async submitForm() {
    const authStore = useAuthStore();
    const csrfToken = authStore.getCsrfToken();

    const formData = new FormData();
    const emailElement = this.$refs.email as HTMLInputElement; // Reactive reference to the email field as it updates
    const passwordElement1 = this.$refs.password1 as HTMLInputElement;
    const passwordElement2 = this.$refs.password2 as HTMLInputElement; // Two password fields for comparison

    // Clear previous error messages
    this.errorMessage = '';

    if (emailElement?.value) {
      formData.append('email', emailElement.value);
      this.change_counter = true;
    }

    if (passwordElement1?.value && passwordElement2?.value) {
      if (passwordElement1.value === passwordElement2.value) {
        formData.append('password', passwordElement1.value);
        this.change_counter = true;
      } else {
        // Set error message if passwords do not match
        this.errorMessage = 'The passwords do not match. Please try again.';
        this.submissionStatus = 'error';
        return;  // Exit the function to prevent submission
      }
    }

    // Check if any changes were made to the form before submitting
    if (!this.change_counter) {
      this.submissionStatus = 'error';
      this.errorMessage = 'No changes were made to the profile.';
      return;  // Exit if no changes were made
    }

    try {
      const response = await fetch('http://localhost:8000/users/', {
        method: 'POST',
        headers: {
          'X-Csrftoken': csrfToken,
        },
        credentials: 'include',
        body: formData,
      });

      // Handle the possible responses from the backend
      if (response.ok) {
        this.submissionStatus = 'success';
        await authStore.checkAuthenticationStatus();
      } else {
        this.submissionStatus = 'error';
        this.errorMessage = 'Failed to update the profile.';
      }
    } catch (error) {
      this.submissionStatus = 'error';
      this.errorMessage = 'An error occurred during the submission.';
    }
  }
},
});
</script>

<style scoped>

  /* Styling for the profile form */
  .profile-container {
      background: #fdfdfd;
      max-width: 600px;
      margin: 20px auto;
      padding: 20px;
      border-radius: 10px;
      border: 1px solid black;
  }

  /* Display the elements as a column */
  .profile-form {
      display: flex;
      flex-direction: column;
  }

  /* Create a gap between the bottom of the container group */
  .form-group {
      margin-bottom: 20px;
  }

  /* Position the labels and setting the colour/weight */
  label {
    margin-left: 5px;
    margin-top: 10px;
    font-weight: bold;
    color: #333;
  }

  /* Styling the available input fields we know exist */
  input[type="email"], input[type="password"] {
      width: 100%;
      padding: 8px;
      margin: 5px 0 20px 0;
      display: inline-block;
      border: 1px solid #ccc;
      border-radius: 4px;
      box-sizing: border-box;
  }

  input:hover{
    border-color: black;
  }

  /* Custom submit button to match the group */
  .submit-button {
      background-color: #fdfdfd;
      padding: 14px 20px;
      margin: 8px 0;
      border: 1px solid black;
      border-radius: 4px;
      cursor: pointer;
      font-weight: 900;
      font-size: 20px;
      text-transform: uppercase;
      font-family:'Lucida Sans', 'Lucida Sans Regular', 'Lucida Grande', 'Lucida Sans Unicode', Geneva, Verdana, sans-serif;
  }

  .submit-button:hover {
    color: green;
    border-color: green;
  }

  /* Error/Success handling styles */
  .success-message, .error-message {
      text-align: center;
      margin-top: 15px;
      font-weight: bold;
      padding: 10px;
      border-radius: 4px;
  }

  .success-message {
      color: #28a745;
  }

  .error-message {
      color: #dc3545;
  }
</style>