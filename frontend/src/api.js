import axios from "axios";

// グローバルIPの設定を統一
axios.defaults.baseURL = "http://111.108.31.73";

// APIエクスポート
export const login = (username, password) =>
  axios.post("/login", { username, password });

export const uploadFile = (file, folder) => {
  const formData = new FormData();
  formData.append("file", file);
  if (folder) {
    formData.append("folder", folder);
  }
  return axios.post("/upload", formData);
};

export const fetchFiles = (folder = "") =>
  axios.get(`/files${folder ? `?folder=${encodeURIComponent(folder)}` : ""}`);

export const deleteFile = (filename) => axios.delete(`/delete/${filename}`);

export const deleteFolder = (foldername) =>
  axios.delete(`/delete-folder/${encodeURIComponent(foldername)}`);

export const checkSession = () => axios.get("/session");

export const logout = () => axios.post("/logout");

export const createFolder = (foldername) =>
  axios.post(`/create-folder/${encodeURIComponent(foldername)}`);
