<template>
  <div class="p-4">
    <form @submit.prevent="login">
      <input
        type="text"
        v-model="username"
        placeholder="Username"
        class="border p-2 w-full mb-4"
      />
      <input
        type="password"
        v-model="password"
        placeholder="Password"
        class="border p-2 w-full mb-4"
      />
      <button type="submit" class="bg-blue-500 text-white py-2 px-4">
        Login
      </button>
    </form>
  </div>
</template>

<script>
import apiClient from "@/services/api";

export default {
  data() {
    return {
      username: "",
      password: "",
    };
  },
  methods: {
    async login() {
      try {
        const response = await apiClient.post("/login", {
          username: this.username,
          password: this.password,
        });
        console.log(response.data.message);
      } catch (error) {
        console.error(error.response.data.message);
      }
    },
  },
};
</script>
