<template src="./FileManagerTemplate.vue"></template>
<script>
import {
    login,
    uploadFile,
    fetchFiles,
    deleteFile,
    deleteFolder,
    checkSession,
    logout,
    createFolder,
    fetchUserAndUpdates,
    saveUpdate,
    renameItem,
    moveFile,
    
} from "@/services/api";
import { marked } from "marked";
import axios from "axios";
import * as XLSX from 'xlsx';

export default {
    data() {
        return {
            username: "",
            password: "",
            loggedIn: false,
            loginError: "",
            files: [],
            folders: [],
            allFolders: [],
            filteredFiles: [],
            selectedFile: null,
            uploadMessage: "",
            folderMessage: "",
            previewUrl: "",
            previewContent: '',   // TXTファイルなどのテキスト内容
            downloadUrl: "", // 個別に設定が必要
            selectedCategory: "all",
            currentFolder: "",
            selectedUploadFolder: "",
            newFolderName: "",
            uploadProgress: -1,
            showMoveModal: false,
            selectedFileForMove: "",
            selectedMoveFolder: "",
            showRenameModal: false,
            renameItemPath: '',
            renameOriginalName: '',
            renameNewName: '',
            renameType: '',
            showNewYear: false, // 演出の表示フラグ
            showExcelModal: false, // Excelプレビュー用
            excelData: [], // Excelファイルのデータ
            excelColumns: [], // Excelファイルのカラム
            sheets: {}, // シートデータを保持
            selectedSheet: "", // 現在選択されているシート
            updateContent: "",
            isAdmin: false,
            isEditMode: false,
            renderedHtml: "",
            showEditModal: false, // 編集モーダル表示フラグ
            editFileContent: "", // 編集中のファイル内容
            editFileName: "", // 編集中のファイル名
            editFilePath: "", // 編集中のファイルパス
        };
    },

    async mounted() {
        try {
            this.loggedIn = false;
            this.isAdmin = false;

            const response = await this.checkSession();
            if (response.loggedIn) {
                this.loggedIn = true;
                this.username = response.username;

                if (!this.currentFolder) {
                    this.currentFolder = "";
                }
                await this.fetchFiles(this.currentFolder);

                this.allFolders = await this.getAllFolders();
            }

            // New Year 演出
            const today = new Date();
            if (today.getMonth() === 0 && today.getDate() === 1) {
                this.showNewYear = true;
                console.log("New Year Event Triggered:", this.showNewYear);

                setTimeout(() => {
                    this.showNewYear = false;
                }, 10000);
            } else {
                console.log("New Year Event Not Triggered. Current Date:", today);
            }

            if (this.loggedIn) {
                await this.fetchUserAndUpdates();
            }
        } catch (error) {
            console.error("Session check failed or API error occurred:", error);
            this.isAdmin = false;
            this.loggedIn = false;
        }
    },

    methods: {

        skipNewYear() {
            this.showNewYear = false;
            console.log("New Year Event Manually Skipped");
        },

        async login() {
            try {
                await login(this.username, this.password);
                this.loggedIn = true;
                this.loginError = "";
                await this.fetchFiles();
                await this.fetchUserAndUpdates();
            } catch (error) {
                this.loginError = error.response?.data?.message || "Login failed.";
            }
        },

        async fetchUserAndUpdates() {
            try {
                const { user, updates } = await fetchUserAndUpdates();
                this.isAdmin = user.role === "admin";

                if (updates) {
                    this.updateContent = updates;
                    await this.renderMarkdown();
                } else {
                    this.updateContent = "No updates available.";
                    this.renderedHtml = "No updates available.";
                }
            } catch (error) {
                console.error("Error fetching user or updates:", error);
                this.isAdmin = false;
                this.updateContent = "No updates available.";
                this.renderedHtml = "No updates available.";
            }
        },

        async checkSession() {
            try {
                const response = await axios.get("/session");
                return response.data;
            } catch (error) {
                console.error("Session Check Failed:", error.response?.data || error);
                return { loggedIn: false };
            }
        },

        toggleEditMode() {
            if (this.isAdmin) {
                this.isEditMode = !this.isEditMode;
            } else {
                alert("権限がありません。");
            }
        },

        async saveUpdate() {
            try {
                await saveUpdate(this.updateContent);
                alert("保存が完了しました。");
                this.isEditMode = false;
            } catch (error) {
                console.error("Error saving update:", error);
                alert("保存に失敗しました。もう一度試してください。");
            }
        },

        async openEditModal(filePath, fileName) {
            try {
                const response = await axios.get(`/download/${encodeURIComponent(filePath)}`, {
                    responseType: "text",
                });
                this.editFileContent = response.data;
                this.editFileName = fileName;
                this.editFilePath = filePath;
                this.showEditModal = true;
            } catch (error) {
                console.error("Failed to load file content for editing:", error);
                alert("ファイルの読み込みに失敗しました。");
            }
        },

        cancelEdit() {
            this.showEditModal = false;
            this.editFileContent = "";
            this.editFileName = "";
            this.editFilePath = "";
        },

        async saveFile() {
            try {
                await axios.post("/api/save-file", {
                    path: this.editFilePath,
                    content: this.editFileContent,
                });
                alert("ファイルが保存されました。");
                this.cancelEdit();
            } catch (error) {
                console.error("Failed to save file:", error);
                alert("ファイルの保存に失敗しました。");
            }
        },

        async logout() {
            try {
                await axios.post('/logout');
                // ログイン状態と権限情報を完全リセット
                this.loggedIn = false;
                this.username = "";
                this.isAdmin = false;
                this.isEditMode = false;
                this.updateContent = "";
                this.previewUrl = "";
                this.selectedFile = null;
                this.folders = [];
                this.files = [];
                this.allFolders = [];
                this.uploadMessage = "";
                this.folderMessage = "";
                this.selectedCategory = "all";
                this.currentFolder = "";
                this.selectedUploadFolder = "";
                this.selectedFileForMove = "";
                this.selectedMoveFolder = "";
                this.uploadProgress = -1;
                this.showExcelModal = false;
                this.excelData = [];
                this.excelColumns = [];
            } catch (error) {
                console.error("Logout failed:", error);
            }
        },
        watch: {
            loggedIn(newVal) {
                if (newVal) {
                    this.fetchUserAndUpdates();
                } else {
                    this.isAdmin = false;
                    this.updateContent = "No updates available.";
                    this.renderMarkdown();
                }
            },
        },

        async fetchFiles(folder = "") {
            try {
                const response = await fetchFiles(folder);
                this.folders = response.data.folders || [];
                this.files = {
                    images: response.data.files.filter(file => this.isImage(file.name)),
                    videos: response.data.files.filter(file => this.isVideo(file.name)),
                    audio: response.data.files.filter(file => this.isAudio(file.name)),
                    others: response.data.files.filter(file => !(
                        this.isImage(file.name) ||
                        this.isVideo(file.name) ||
                        this.isAudio(file.name)
                    )),
                };
                this.currentFolder = folder;
                this.filterFiles();
            } catch (error) {
                console.error("Failed to fetch files:", error);
                this.folders = [];
                this.files = { images: [], videos: [], audio: [], others: [] };
                this.filteredFiles = [];
            }
        },

        async createFolder() {
            if (!this.newFolderName) {
                this.folderMessage = "フォルダ名を入力してください。";
                this.clearMessageAfterDelay("folderMessage");
                return;
            }

            try {
                const response = await createFolder({
                    foldername: this.newFolderName,
                    base_folder: this.currentFolder || "",
                });

                this.folderMessage = response.message;
                await this.fetchFiles(this.currentFolder);
                this.allFolders = await this.getAllFolders();

                this.clearMessageAfterDelay("folderMessage");
            } catch (error) {
                if (error.response && error.response.status === 409) {
                    this.folderMessage = `Folder '${this.newFolderName}' already exists.`;
                } else {
                    this.folderMessage = "フォルダの作成に失敗しました。";
                }
                this.clearMessageAfterDelay("folderMessage");
            }
        },

        clearMessageAfterDelay(messageField, delay = 5000) {
            setTimeout(() => {
                this[messageField] = "";
            }, delay);
        },

        goToParent() {
            if (this.currentFolder) {
                const parentFolder = this.currentFolder.split("/").slice(0, -1).join("/");
                this.fetchFiles(parentFolder);
            }
        },

        async uploadFile() {
            if (!this.selectedFile) {
                this.uploadMessage = "初めにファイルを選択してください。";
                return;
            }

            this.uploadProgress = 0;

            try {
                const response = await uploadFile(
                    this.selectedFile,
                    this.selectedUploadFolder || "",
                    (progress) => {
                        this.uploadProgress = progress;
                        console.log(`Upload progress: ${progress}%`);
                    }
                );

                this.uploadMessage = response.data.message || "アップロードが完了しました。";
                this.selectedFile = null;
                this.$refs.fileInput.value = "";
                this.selectedUploadFolder = "";
                this.uploadProgress = -1;
                await this.fetchFiles(this.currentFolder);

                setTimeout(() => {
                    this.uploadMessage = "";
                }, 5000);
            } catch (error) {
                console.error("Error during file upload:", error);
                this.uploadMessage =
                    error.response?.data?.message || "アップロードに失敗しました。";
                this.uploadProgress = -1;
            }
        },

        async deleteFolder(folderPath) {
            if (!confirm(`"${folderPath}" を削除しますか？`)) {
                return;
            }

            this.folders = this.folders.filter(folder => folder.path !== folderPath);
            try {
                const response = await deleteFolder(folderPath);
                alert(response.message);

                await this.fetchFiles(this.currentFolder);
                this.allFolders = await this.getAllFolders();
            } catch (error) {
                console.error("Failed to delete folder:", error);
                alert("削除に失敗しました。");
            }
        },

        resetTableStyles() {
            const table = document.querySelector("#excelTable");
            if (table) {
                const headers = table.querySelectorAll("th");
                headers.forEach((header) => {
                    header.style.width = "";
                });

                const rows = table.querySelectorAll("tr");
                rows.forEach((row) => {
                    row.style.height = "";
                });
            }
        },

        async previewExcel(filePath) {
            try {
                this.resetTableStyles();

                const response = await axios.get(`/download/${encodeURIComponent(filePath)}`, {
                    responseType: "blob",
                });

                const fileData = await response.data.arrayBuffer();
                const workbook = XLSX.read(fileData, { type: "array" });

                this.sheets = workbook.SheetNames.reduce((acc, sheetName) => {
                    const sheetData = XLSX.utils.sheet_to_json(workbook.Sheets[sheetName], { header: 1 });
                    acc[sheetName] = sheetData;
                    return acc;
                }, {});

                this.selectedSheet = workbook.SheetNames[0];
                this.updateExcelTable();

                this.showExcelModal = true;
            } catch (error) {
                console.error("Excelファイルのプレビューに失敗しました。:", error);
                alert("Excelファイルのプレビューに失敗しました。");
            }
        },

        //列ヘッダー生成用メソッド
        generateExcelColumns(columnsCount) {
            const columns = [];
            for (let i = 0; i < columnsCount; i++) {
                let columnName = "";
                let col = i;
                do {
                    columnName = String.fromCharCode((col % 26) + 65) + columnName;
                    col = Math.floor(col / 26) - 1;
                } while (col >= 0);
                columns.push(columnName);
            }
            return columns;
        },

        updateExcelTable() {
            if (this.selectedSheet && this.sheets[this.selectedSheet]) {
                const sheetData = this.sheets[this.selectedSheet];
                const rowsCount = Math.max(sheetData.length, 20); // デフォルト行数を20に設定
                const columnsCount = Math.max(
                    ...sheetData.map(row => row.length),
                    17 // 最低Q列分を確保
                );

                this.excelColumns = this.generateExcelColumns(columnsCount);
                this.excelData = Array.from({ length: rowsCount }, (_, rowIndex) => {
                    return Array.from({ length: columnsCount }, (_, colIndex) => {
                        return sheetData[rowIndex]?.[colIndex] || ""; // データがない場合は空白を埋める
                    });
                });

                setTimeout(() => this.enableResizableCells(), 0);
            }
        },

        enableResizableCells() {
            const table = document.querySelector("#excelTable");
            if (!table) return;

            const headers = table.querySelectorAll("th");
            headers.forEach((header) => {
                const resizer = document.createElement("div");
                resizer.className = "resize-handle-horizontal";
                resizer.addEventListener("mousedown", this.startColumnResize);
                header.appendChild(resizer);
            });

            const rows = table.querySelectorAll("tr");
            rows.forEach((row) => {
                const rowNumberCell = row.querySelector(".row-number");
                if (rowNumberCell) {
                    const resizer = document.createElement("div");
                    resizer.className = "resize-handle-vertical";
                    resizer.addEventListener("mousedown", this.startRowResize);
                    rowNumberCell.appendChild(resizer);
                }
            });

            const cells = table.querySelectorAll("td");
            cells.forEach((cell) => {
                const horizontalResizer = document.createElement("div");
                horizontalResizer.className = "resize-handle-horizontal";
                horizontalResizer.addEventListener("mousedown", (event) =>
                    this.startColumnResize(event, cell)
                );
                cell.appendChild(horizontalResizer);

                const verticalResizer = document.createElement("div");
                verticalResizer.className = "resize-handle-vertical";
                verticalResizer.addEventListener("mousedown", (event) =>
                    this.startRowResize(event, cell)
                );
                cell.appendChild(verticalResizer);
            });
        },

        startColumnResize(event, targetCell = null) {
            const th = targetCell
                ? targetCell
                : event.target.parentElement;
            const table = th.closest("table");
            const startX = event.pageX;
            const columnIndex = Array.from(th.parentElement.children).indexOf(th);
            const startWidth = th.offsetWidth;

            let animationFrameId;

            document.body.classList.add("dragging");

            const mouseMoveHandler = (e) => {
                const newWidth = Math.max(startWidth + (e.pageX - startX), 30);
                if (!animationFrameId) {
                    animationFrameId = requestAnimationFrame(() => {
                        table.querySelectorAll(
                            `td:nth-child(${columnIndex + 1}), th:nth-child(${columnIndex + 1})`
                        ).forEach((cell) => (cell.style.width = `${newWidth}px`));
                        animationFrameId = null;
                    });
                }
            };

            const mouseUpHandler = () => {
                document.body.classList.remove("dragging");
                document.removeEventListener("mousemove", mouseMoveHandler);
                document.removeEventListener("mouseup", mouseUpHandler);
                if (animationFrameId) {
                    cancelAnimationFrame(animationFrameId);
                }
            };

            document.addEventListener("mousemove", mouseMoveHandler);
            document.addEventListener("mouseup", mouseUpHandler);
        },

        startRowResize(event, targetCell = null) {
            const row = targetCell
                ? targetCell.parentElement
                : event.target.closest("tr");
            const table = row.closest("table");
            const startY = event.pageY;
            const rowIndex = Array.from(row.parentElement.children).indexOf(row);
            const startHeight = row.offsetHeight;

            let animationFrameId;

            document.body.classList.add("dragging");

            const mouseMoveHandler = (e) => {
                const newHeight = Math.max(20, startHeight + (e.pageY - startY));
                if (!animationFrameId) {
                    animationFrameId = requestAnimationFrame(() => {
                        table.querySelectorAll(
                            `tr:nth-child(${rowIndex + 1}) td, tr:nth-child(${rowIndex + 1}) th`
                        ).forEach((cell) => (cell.style.height = `${newHeight}px`));
                        animationFrameId = null;
                    });
                }
            };

            const mouseUpHandler = () => {
                document.body.classList.remove("dragging");
                document.removeEventListener("mousemove", mouseMoveHandler);
                document.removeEventListener("mouseup", mouseUpHandler);
                if (animationFrameId) {
                    cancelAnimationFrame(animationFrameId);
                }
            };

            document.addEventListener("mousemove", mouseMoveHandler);
            document.addEventListener("mouseup", mouseUpHandler);
        },

        async previewFile(filePath) {
            try {
                const encodedPath = encodeURIComponent(filePath.replace(/\\/g, "/"));
                this.previewUrl = `${this.downloadUrl}/${encodedPath}`;
                console.log(`Sending preview request to: ${this.previewUrl}`);

                if (this.isMarkdown(filePath)) {
                    await this.previewMarkdown(filePath);
                } else if (this.isExcel(filePath)) {
                    await this.previewExcel(filePath);
                } else if (this.isText(filePath)) {
                    const response = await axios.get(this.previewUrl, { responseType: "text" });
                    this.previewContent = response.data;
                } else {
                    const response = await axios.get(this.previewUrl);
                    console.log("Preview response:", response);
                }
            } catch (error) {
                console.error("Failed to preview file:", error);
                alert(`プレビュー中にエラーが発生しました。: ${error.message}`);
            }
        },

        renderMarkdown: async function () {
            try {
                if (!this.updateContent || this.updateContent.trim() === "") {
                    this.renderedHtml = "";
                    return;
                }
                const safeContent = typeof this.updateContent === "string" ? this.updateContent : "";

                const renderer = new marked.Renderer();
                renderer.list = function (body, ordered) {
                    const type = ordered ? "ol" : "ul";
                    return `<${type}>${body}</${type}>`;
                };

                marked.setOptions({
                    breaks: true,
                    gfm: true,
                    tables: true,
                    renderer,
                });

                this.renderedHtml = marked(safeContent);
            } catch (error) {
                console.error("renderMarkdown: Error rendering Markdown content:", error);
            }
        },

        async previewMarkdown(filePath) {
            try {
                this.previewContent = "";
                this.markdownHtml = "";

                const response = await axios.get(`/download/${encodeURIComponent(filePath)}`, {
                    responseType: "text",
                });

                const safeContent = typeof response.data === "string" ? response.data : "";

                const renderer = new marked.Renderer();

                marked.setOptions({
                    breaks: true,
                    gfm: true,
                    tables: true,
                    renderer,
                });

                this.markdownHtml = marked(safeContent);
                this.previewUrl = filePath;
            } catch (error) {
                console.error("previewMarkdown: Error previewing Markdown file:", error);
                alert("Markdown プレビューに失敗しました。");
            }
        },

        downloadFile(filePath) {
            const encodedPath = encodeURIComponent(filePath.replace(/\\/g, "/"));
            const downloadUrl = `${this.downloadUrl}/${encodedPath}`;
            window.open(downloadUrl, '_blank');
        },

        closePreview() {
            this.previewUrl = "";
            this.previewContent = '';
            this.showExcelModal = false;
            this.excelData = [];
            this.excelColumns = [];
        },

        confirmDelete(file) {
            if (confirm(`${file}を削除してよろしいですか？`)) {
                this.deleteFile(file);
            }
        },

        async getAllFolders(baseFolder = "") {
            try {
                const response = await fetchFiles(baseFolder);
                const currentFolders = response.data.folders || [];
                let allFolders = currentFolders.map(folder =>
                    baseFolder ? `${baseFolder}/${folder.name}` : folder.name
                );

                for (const folder of currentFolders) {
                    const subFolderPath = baseFolder ? `${baseFolder}/${folder.name}` : folder.name;
                    const subFolders = await this.getAllFolders(subFolderPath);
                    allFolders = allFolders.concat(subFolders);
                }

                return allFolders;
            } catch (error) {
                console.error("Failed to fetch all folders:", error);
                alert("一覧の取得に失敗しました。更新を試してください。");
                return [];
            }
        },

        openMoveModal(filePath) {
            this.selectedFileForMove = filePath;
            this.showMoveModal = true;
        },
        cancelMove() {
            this.selectedFileForMove = "";
            this.selectedMoveFolder = "";
            this.showMoveModal = false;
            console.log("Move modal canceled and state cleared.");
        },

        openRenameModal(itemPath, originalName, type) {
            this.renameItemPath = itemPath;
            this.renameType = type;
            this.renameOriginalName = originalName;

            if (type === "file") {
                this.renameNewName = originalName.replace(/\.[^/.]+$/, "");
            } else {
                this.renameNewName = originalName;
            }

            this.showRenameModal = true;
        },

        cancelRename() {
            this.renameItemPath = '';
            this.renameOriginalName = '';
            this.renameNewName = '';
            this.renameType = '';
            this.showRenameModal = false;
        },

        async renameItem() {
            try {
                const newName = this.renameType === "file"
                    ? `${this.renameNewName}.${this.renameOriginalName.split(".").pop()}`
                    : this.renameNewName;

                await renameItem(this.renameItemPath, newName, this.renameType);
                alert("リネームが完了しました。");
                this.cancelRename();
                this.fetchFiles(this.currentFolder);
            } catch (error) {
                console.error("Error renaming item:", error);
                alert("リネームに失敗しました。");
            }
        },

        async moveFile() {
            try {
                await moveFile(this.selectedFileForMove, this.selectedMoveFolder);
                alert("移動が完了しました。");
                this.cancelMove();
                this.fetchFiles(this.currentFolder);
            } catch (error) {
                console.error("Error moving file:", error);
                alert("移動に失敗しました。");
            }
        },

        onFileChange(event) {
            this.selectedFile = event.target.files[0];
            if (this.selectedFile) {
                console.log("Selected file:", this.selectedFile.name);
            }
        },
        async deleteFile(filePath) {
            try {
                const response = await deleteFile(filePath);
                alert(response.message);
                await this.fetchFiles(this.currentFolder);
            } catch (error) {
                console.error("Failed to delete file:", error);
                alert("削除に失敗しました。");
            }
        },

        filterFiles() {
            if (this.selectedCategory === "all") {
                this.filteredFiles = Object.values(this.files).flat();
            } else {
                this.filteredFiles = this.files[this.selectedCategory] || [];
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
        isText(fileUrl) {
            return /\.txt$/i.test(fileUrl);
        },
        isMarkdown(fileUrl) {
            return /\.(md|markdown)$/i.test(fileUrl);
        },
        isExcel(fileUrl) {
            return /\.(xlsx|xls)$/i.test(fileUrl);
        },
        isPDF(fileUrl) {
            return /\.pdf$/i.test(fileUrl);
        },
    },
};
</script>
<style src="./FileManagerStyle.css"></style>