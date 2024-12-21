import axios from "axios";

// グローバルIPの設定を統一
axios.defaults.baseURL = "http://111.108.31.73";

// APIエクスポート
export const login = (username, password) =>
  axios.post("/login", { username, password });

export const uploadFile = (file) => {
  const formData = new FormData();
  formData.append("file", file);
  return axios.post("/upload", formData);
};

export const fetchFiles = () => axios.get("/files");

export const deleteFile = (filename) => axios.delete(`/delete/${filename}`);
