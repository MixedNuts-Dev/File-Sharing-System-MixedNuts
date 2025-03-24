import axios from "axios";

// ※baseURLはプロジェクトに応じて設定してください
// axios.defaults.baseURL = "https://your.domain.com"; // ← 必要に応じて有効化

// ログイン
export const login = async (username, password) => {
  try {
    const response = await axios.post("/login", { username, password });
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.message || "Login failed.");
  }
};

// セッション確認
export const checkSession = () => axios.get("/session");

// ログアウト
export const logout = () => axios.post("/logout");

// ファイルアップロード
export const uploadFile = (file, folder, onUploadProgress) => {
  const formData = new FormData();
  formData.append("file", file);
  if (folder) formData.append("folder", folder);

  return axios.post("/upload", formData, {
    onUploadProgress: (event) => {
      const percent = Math.round((event.loaded * 100) / event.total);
      if (onUploadProgress) onUploadProgress(percent);
    },
  });
};

// ファイル一覧取得
export const fetchFiles = (folder = "") =>
  axios.get(`/files${folder ? `?folder=${encodeURIComponent(folder)}` : ""}`);

// ファイル削除
export const deleteFile = async (filePath) => {
  try {
    const response = await axios.delete("/delete", {
      data: { path: filePath },
    });
    return response.data;
  } catch (error) {
    console.error("deleteFile failed:", error);
    throw error;
  }
};

// フォルダ削除
export const deleteFolder = async (folderPath) => {
  try {
    const response = await axios.delete("/delete", {
      data: { path: folderPath },
    });
    return response.data;
  } catch (error) {
    console.error("deleteFolder failed:", error);
    throw error;
  }
};

// フォルダ作成
export const createFolder = (data) => axios.post("/create-folder", data);

// ユーザー情報とシステムアップデートの取得
export const fetchUserAndUpdates = async () => {
  const userRes = await axios.get("/api/user");
  const updateRes = await axios.get("/api/system-updates");
  return {
    user: userRes.data,
    updates: updateRes.data.content,
  };
};

// システムアップデート保存（管理者用）
export const saveUpdate = async (content) => {
  const response = await axios.post("/api/system-updates", { content });
  return response.data;
};

// ファイル／フォルダのリネーム
export const renameItem = async (path, newName, type) => {
  const response = await axios.post("/rename", {
    path,
    new_name: newName,
    type,
  });
  return response.data;
};

// ファイルの移動
export const moveFile = async (srcPath, destFolder) => {
  const response = await axios.post("/move", {
    src_path: srcPath,
    dest_folder: destFolder,
  });
  return response.data;
};
