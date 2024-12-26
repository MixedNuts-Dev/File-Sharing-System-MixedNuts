<template>
  <div id="app" class="p-4">
    <h1 class="text-2xl font-bold mb-4">File Sharing System</h1>

    <!-- Login Section -->
    <div v-if="!loggedIn" class="mb-4">
      <h2 class="text-xl mb-2">Login</h2>
      <input
        v-model="username"
        placeholder="Username"
        class="border p-2 mr-2"
        @keyup.enter="login"
      />
      <input
        v-model="password"
        type="password"
        placeholder="Password"
        class="border p-2 mr-2"
        @keyup.enter="login"
      />
      <button @click="login" class="bg-blue-500 text-white px-4 py-2">Login</button>
      <p v-if="loginError" class="text-red-500 mt-2">{{ loginError }}</p>
    </div>

    <!-- File Management Section -->
    <div v-else>
      <h2 class="text-xl mb-2">Welcome, {{ username }}</h2>
      <button @click="logout" class="bg-red-500 text-white px-4 py-2 mb-4">Logout</button>

      <!-- Back to Root Button -->
      <button v-if="currentFolder" @click="goToRoot" class="bg-gray-500 text-white px-4 py-2 mb-4">
        Back to Root
      </button>

      <!-- Folder Creation Section -->
      <div>
        <h2 class="text-xl mb-2">Create a Folder</h2>
        <input v-model="newFolderName" placeholder="Folder name" class="border p-2 mr-2" />
        <button @click="createFolder" class="bg-green-500 text-white px-4 py-2">Create</button>
        <p v-if="folderMessage" class="mt-2">{{ folderMessage }}</p>
      </div>

      <!-- File Upload Section -->
      <h2 class="text-xl mb-2 mt-4">Upload a File</h2>
      <input type="file" @change="onFileChange" class="border p-2 mr-2" />
      <select v-model="selectedUploadFolder" class="border p-2 mr-2">
        <option value="">Root</option>
        <option v-for="folder in allFolders" :key="folder" :value="folder">
          {{ folder }}
        </option>
      </select>
      <button @click="uploadFile" class="bg-green-500 text-white px-4 py-2">Upload</button>
      <p v-if="uploadMessage" class="mt-2">{{ uploadMessage }}</p>

      <!-- Category Filter -->
      <div class="mt-4">
        <label for="category">Filter by category:</label>
        <select v-model="selectedCategory" @change="filterFiles" id="category" class="ml-2 border">
          <option value="all">All</option>
          <option value="images">Images</option>
          <option value="videos">Videos</option>
          <option value="audio">Audio</option>
          <option value="others">Others</option>
        </select>
      </div>

      <!-- File and Folder List Section -->
      <h2 class="text-xl mt-4 mb-2">Available Files and Folders</h2>
      <ul>
        <li v-for="folder in folders" :key="folder" class="mb-2">
          <span class="text-blue-600 mr-2 cursor-pointer" @click="fetchFiles(folder)">📁 {{ folder }}</span>
          <button class="ml-2 bg-red-500 text-white px-2 py-1" @click="deleteFolder(folder)">
            Delete Folder
          </button>
        </li>
        <li v-for="file in filteredFiles" :key="file" class="mb-2">
          <!-- 修正されたダウンロードリンク -->
          <a
            :href="`${downloadUrl}/${encodeURIComponent(file)}${currentFolder ? `?folder=${encodeURIComponent(currentFolder)}` : ''}`"
            class="text-blue-600 mr-2"
            download
          >
            {{ file }}
          </a>
          <button class="ml-2 bg-gray-300 text-black px-2 py-1" @click="previewFile(file)">Preview</button>
          <button class="ml-2 bg-red-500 text-white px-2 py-1" @click="confirmDelete(file)">Delete</button>
        </li>
      </ul>
    </div>

    <!-- Preview Section -->
    <div v-if="previewUrl" class="mt-4 border p-2">
      <template v-if="isImage(previewUrl)">
        <img :src="previewUrl" alt="Preview" class="border w-full" />
      </template>
      <template v-else-if="isVideo(previewUrl)">
        <video :src="previewUrl" class="border" width="640" height="360" controls></video>
      </template>
      <template v-else-if="isAudio(previewUrl)">
        <audio :src="previewUrl" class="border w-full" controls></audio>
      </template>
      <button @click="closePreview" class="block mt-2 bg-red-500 text-white px-4 py-2">Close Preview</button>
    </div>
  </div>
</template>


<script>
import { login, uploadFile, fetchFiles, deleteFile, checkSession, logout, createFolder, deleteFolder } from "./api";

export default {
  data() {
    return {
      username: "",
      password: "",
      loggedIn: false,
      loginError: "",
      files: {
        images: [],
        videos: [],
        audio: [],
        others: [],
      },
      folders: [],
      allFolders: [], // 全フォルダを保持
      filteredFiles: [],
      selectedFile: null,
      uploadMessage: "",
      folderMessage: "",
      previewUrl: "",
      downloadUrl: "http://111.108.31.73/download",
      selectedCategory: "all",
      currentFolder: "",
      selectedUploadFolder: "", // アップロード先のフォルダを保持
      newFolderName: "",
    };
  },
  async mounted() {
    try {
      const response = await checkSession();
      if (response.data.loggedIn) {
        this.loggedIn = true;
        this.username = response.data.username;
        await this.fetchFiles();
        this.allFolders = await this.getAllFolders();
      }
    } catch (error) {
      console.error("Session check failed:", error);
    }
  },
  methods: {
    async login() {
      try {
        await login(this.username, this.password);
        this.loggedIn = true;
        this.loginError = "";
        await this.fetchFiles();
        this.allFolders = await this.getAllFolders();
      } catch (error) {
        this.loginError = error.response?.data?.message || "Login failed.";
      }
    },
    async logout() {
      try {
        await logout();
        this.loggedIn = false;
        this.username = "";
        this.previewUrl = ""; // ログアウト時にプレビューを閉じる
        this.selectedFile = null; // アップロード中のファイルをリセット
      } catch (error) {
        console.error("Logout failed:", error);
      }
    },
    async fetchFiles(folder = "") {
      try {
        const response = await fetchFiles(folder);
        this.folders = response.data.folders || [];
        this.files = response.data.files || [];
        this.currentFolder = folder; // 現在のフォルダを設定
        this.filterFiles();
      } catch (error) {
        console.error("Failed to fetch files:", error);
        this.folders = [];
        this.files = { images: [], videos: [], audio: [], others: [] };
      }
    },
    async getAllFolders(baseFolder = "") {
      try {
        const response = await fetchFiles(baseFolder);
        const currentFolders = response.data.folders || [];
        let allFolders = [...currentFolders.map(folder => baseFolder ? `${baseFolder}/${folder}` : folder)];

        // 再帰的にサブフォルダを取得
        for (const folder of currentFolders) {
          const subFolderPath = baseFolder ? `${baseFolder}/${folder}` : folder;
          const subFolders = await this.getAllFolders(subFolderPath);
          allFolders = allFolders.concat(subFolders);
        }

        return allFolders;
      } catch (error) {
        console.error("Failed to fetch all folders:", error);
        return [];
      }
    },
    async deleteFolder(folder) {
      if (!confirm(`Are you sure you want to delete the folder "${folder}" and all its contents?`)) {
        return;
      }
      try {
        const response = await deleteFolder(folder);
        alert(response.data.message);
        await this.fetchFiles(this.currentFolder); // 現在のフォルダを更新
        this.allFolders = await this.getAllFolders();
      } catch (error) {
        console.error("Failed to delete folder:", error);
        alert("Failed to delete folder.");
      }
    },
    goToRoot() {
      this.currentFolder = ""; // Rootに戻る
      this.fetchFiles(); // ファイルを更新
    },
    filterFiles() {
      if (this.selectedCategory === "all") {
        this.filteredFiles = Object.values(this.files).flat();
      } else {
        this.filteredFiles = this.files[this.selectedCategory];
      }
    },
    onFileChange(event) {
      this.selectedFile = event.target.files[0];
    },
    async uploadFile() {
      if (!this.selectedFile) {
        this.uploadMessage = "Please select a file first.";
        return;
      }
      try {
        const response = await uploadFile(this.selectedFile, this.selectedUploadFolder);
        this.uploadMessage = response.data.message;
        await this.fetchFiles(this.currentFolder);
      } catch (error) {
        console.error("File upload failed:", error.response?.data?.message || error.message);
        this.uploadMessage = "File upload failed.";
      }
    },
    async createFolder() {
      if (!this.newFolderName) {
        this.folderMessage = "Please enter a folder name.";
        return;
      }
      try {
        const response = await createFolder(this.newFolderName, this.currentFolder);
        this.folderMessage = response.data.message;
        await this.fetchFiles(this.currentFolder);
        this.allFolders = await this.getAllFolders();
      } catch (error) {
        console.error("Failed to create folder:", error.response?.data?.message || error.message);
        this.folderMessage = "Failed to create folder.";
      }
    },
    // previewFile(file) {
    //   this.previewUrl = `${this.downloadUrl}/${file}`;
    // },

    previewFile(file) {
      const path = this.currentFolder ? `${this.currentFolder}/${file}` : file;
      this.previewUrl = `${this.downloadUrl}/${encodeURIComponent(path)}`;
      this.$nextTick(() => {
        const videoPlayer = this.$refs.videoPlayer;
        if (videoPlayer) {
          videoPlayer.volume = 0.3; // 音量を30%に設定
        }
        const audioPlayer = this.$refs.audioPlayer;
        if (audioPlayer) {
          audioPlayer.volume = 0.3; // 音量を30%に設定
        }
      });
    },

    closePreview() {
      this.previewUrl = ""; // プレビューを閉じる
    },
    confirmDelete(file) {
      if (confirm(`Are you sure you want to delete ${file}?`)) {
        this.deleteFile(file);
      }
    },
    // async deleteFile(file) {
    //   try {
    //     if (this.previewUrl.endsWith(file)) {
    //       this.closePreview(); // プレビューを閉じる
    //     }
    //     const response = await deleteFile(file);
    //     alert(response.data.message);
    //     this.fetchFiles(this.currentFolder);
    //   } catch (error) {
    //     console.error("Failed to delete file:", error);
    //     alert("Failed to delete file.");
    //   }
    // },

    async deleteFile(file) {
        try {
            // プレビュー中のファイルを削除する場合、プレビューを閉じる
            const path = this.currentFolder ? `${this.currentFolder}/${file}` : file;
            if (this.previewUrl.endsWith(encodeURIComponent(path))) {
                this.closePreview(); // プレビューを閉じる
            }
            // ファイル削除リクエストを送信
            const response = await deleteFile(path);
            alert(response.data.message);
            await this.fetchFiles(this.currentFolder); // 現在のフォルダを更新
        } catch (error) {
            console.error("Failed to delete file:", error.response?.data?.message || error.message);
            alert("Failed to delete file.");
        }
    },
    isImage(fileUrl) {
      return /\.(jpg|jpeg|png|gif|bmp|webp)$/i.test(fileUrl);
    },
    isVideo(fileUrl) {
      return /\.(mp4|webm|ogg)$/i.test(fileUrl);
    },
    isAudio(fileUrl) {
      return /\.(mp3|wav|flac|ogg)$/i.test(fileUrl);
    },
  },
};
</script>

<style>
:root {
  --background-color: white;
  --text-color: black;
  --primary-color: #007bff;
  --secondary-color: #6c757d;
  --error-color: #dc3545;
  --link-color: #0056b3;
}

@media (prefers-color-scheme: dark) {
  :root {
    --background-color: #121212;
    --text-color: #f0f0f0;
    --primary-color: #0d6efd;
    --secondary-color: #adb5bd;
    --error-color: #f44336;
    --link-color: #66b2ff;
  }
}

input {
  background-color: var(--background-color);
  color: var(--text-color);
  border: 1px solid var(--secondary-color);
  padding: 0.5rem;
  border-radius: 4px;
}

input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 3px var(--primary-color);
}

select {
  background-color: var(--background-color);
  color: var(--text-color);
  border: 1px solid var(--secondary-color);
  padding: 0.5rem;
  border-radius: 4px;
}

select:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 3px var(--primary-color);
}


body {
  background-color: var(--background-color);
  color: var(--text-color);
  font-family: Arial, sans-serif;
}

.bg-primary {
  background-color: var(--primary-color);
}

.bg-secondary {
  background-color: var(--secondary-color);
}

.bg-error {
  background-color: var(--error-color);
}

.text-link {
  color: var(--link-color);
}

.text-error {
  color: var(--error-color);
}
</style>