<template>
    <div id="app" class="p-4">

        <!-- ログインフォーム -->
        <div v-if="!loggedIn">
            <h2 class="text-xl mb-2">ログイン</h2>
            <input v-model="username" placeholder="Username" class="border p-2 mr-2" @keyup.enter="login"/>
            <input v-model="password" type="password" placeholder="Password" class="border p-2 mr-2"
                @keyup.enter="login" />
            <button @click="login" class="bg-blue-500 text-white px-4 py-2">ログイン</button>
            <p v-if="loginError" class="text-red-500 mt-2">{{ loginError }}</p>
        </div>

        <!-- Happy New Year 演出 -->
        <div v-else-if="showNewYear" class="new-year-container">
            <div class="fireworks-container">
                <div class="c-firework"></div>
                <div class="c-firework"></div>
                <div class="c-firework"></div>
            </div>
            <h1 class="new-year-text">Happy New Year</h1>
            <button @click="skipNewYear" class="close-btn">Skip</button>
        </div>

        <!-- ログイン後の表示 -->
        <div v-else>
            <!-- システムアップデート -->
            <div id="system-updates" class="p-4 mb-4 border rounded bg-gray-100">
                <h2 class="text-xl font-bold mb-4">直近のアップデート</h2>
                <!-- 管理者モード -->
                <div v-if="isAdmin">
                    <div class="flex justify-between items-center">
                        <span class="font-semibold">管理者ページ</span>
                        <button @click="toggleEditMode"
                            :class="['px-4 py-2 rounded', isEditMode ? 'bg-green-500 text-white' : 'bg-blue-500 text-white']">
                            {{ isEditMode ? '編集中' : '編集' }}
                        </button>
                    </div>

                    <!-- 編集モード -->
                    <textarea v-if="isEditMode" v-model="updateContent"
                        class="w-full h-32 border p-2 mt-2 bg-white text-black"></textarea>
                    <button v-if="isEditMode" @click="saveUpdate" class="bg-green-500 text-white px-4 py-2 mt-2">
                        保存
                    </button>

                    <!-- 非編集モード: 一般ユーザーと同じ表示 -->
                    <div v-else>
                        <div v-if="renderedHtml" v-html="renderedHtml" class="p-4 markdown-preview"></div>
                        <div v-else class="text-gray-500">アップデート情報はありません。</div>
                    </div>
                </div>

                <!-- 一般ユーザー表示 -->
                <div v-else>
                    <div v-if="renderedHtml" v-html="renderedHtml" class="p-4 markdown-preview"></div>
                    <div v-else class="text-gray-500">アップデート情報はありません。</div>
                </div>
            </div>

            <!-- ファイル管理セクション -->
            <h2 class="text-xl mb-2">ようこそ！, {{ username }}</h2>
            <button @click="logout" class="bg-red-500 text-white px-4 py-2 mb-4">ログアウト</button>

            <!-- Back to Parent Folder Button -->
            <button v-if="currentFolder" @click="goToParent" class="bg-gray-500 text-white px-4 py-2 mb-4">
                前の階層へ戻る
            </button>

            <!-- フォルダ作成 -->
            <div>
                <h2 class="text-xl mb-2">フォルダ作成</h2>
                <input v-model="newFolderName" placeholder="フォルダ名" class="border p-2 mr-2" />
                <button @click="createFolder" class="bg-green-500 text-white px-4 py-2">作成</button>
                <p v-if="folderMessage" class="mt-2">{{ folderMessage }}</p>
            </div>

            <!-- ファイルアップロード -->
            <h2 class="text-xl mb-2 mt-4">ファイルアップロード</h2>
            <input type="file" @change="onFileChange" ref="fileInput" class="border p-2 mr-2" />
            <select v-model="selectedUploadFolder" class="border p-2 mr-2">
                <option value="">ルート</option>
                <option v-for="folder in allFolders" :key="folder" :value="folder">
                    {{ folder }}
                </option>
            </select>
            <button @click="uploadFile" class="bg-green-500 text-white px-4 py-2">アップロード</button>
            <p v-if="uploadMessage" class="mt-2">{{ uploadMessage }}</p>

            <!-- プログレスバー -->
            <div v-if="uploadProgress >= 0" class="mt-2">
                <p>アップロード進捗: {{ uploadProgress }}%</p>
                <div class="w-full bg-gray-200 rounded">
                    <div class="bg-blue-500 text-white text-center p-1 rounded"
                        :style="{ width: uploadProgress + '%' }">
                        {{ uploadProgress }}%
                    </div>
                </div>
            </div>

            <!-- フィルタリング用のドロップダウン -->
            <div class="mt-4">
                <label for="file-category" class="mr-2">フィルター:</label>
                <select id="file-category" v-model="selectedCategory" @change="filterFiles" class="border p-2">
                    <option value="all">すべて</option>
                    <option value="images">画像</option>
                    <option value="videos">ビデオ</option>
                    <option value="audio">オーディオ</option>
                    <option value="others">その他</option>
                </select>
            </div>

            <!-- ファイルとフォルダリスト -->
            <h2 class="text-xl mt-4 mb-2">ファイル・フォルダ一覧</h2>
            <ul>
                <li v-for="folder in folders" :key="folder.name" class="mb-2">
                    <span class="text-blue-600 mr-2 cursor-pointer" @click="fetchFiles(folder.path)">
                        📁 {{ folder.name }}
                    </span>
                    <button class="ml-2 bg-blue-500 text-white px-2 py-1" @click="openMoveModal(folder.path)">
                        移動
                    </button>
                    <button class="ml-2 bg-yellow-300 text-black px-2 py-1"
                        @click="openRenameModal(folder.path, folder.name, 'folder')">
                        リネーム
                    </button>
                    <button class="ml-2 bg-red-500 text-white px-2 py-1" @click="deleteFolder(folder.path)">
                        削除
                    </button>
                </li>
                <li v-for="file in filteredFiles" :key="file.name" class="mb-2">
                    <a :href="`${downloadUrl}/${encodeURIComponent(file.path)}${currentFolder ? `?folder=${encodeURIComponent(currentFolder)}` : ''}`"
                        class="text-blue-600 mr-2" download>
                        {{ file.name }}
                    </a>
                    <button v-if="isMarkdown(file.name) || isText(file.name)"
                        @click="openEditModal(file.path, file.name)" class="ml-2 bg-yellow-300 text-black px-2 py-1">
                        編集
                    </button>
                    <button class="ml-2 bg-gray-300 text-black px-2 py-1" @click="previewFile(file.path)">
                        プレビュー
                    </button>
                    <button class="ml-2 bg-blue-500 text-white px-2 py-1" @click="openMoveModal(file.path)">
                        移動
                    </button>
                    <button class="ml-2 bg-yellow-300 text-black px-2 py-1"
                        @click="openRenameModal(file.path, file.name, 'file')">
                        リネーム
                    </button>
                    <button class="ml-2 bg-red-500 text-white px-2 py-1" @click="confirmDelete(file.path)">
                        削除
                    </button>
                </li>
            </ul>
        </div>

        <!-- プレビューセクション -->
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

            <template v-if="isText(previewUrl)">
                <div v-html="previewContent" class="text-preview"></div>
            </template>


            <template v-if="previewUrl && isMarkdown(previewUrl)">
                <div v-html="markdownHtml" class="markdown-preview"></div>
            </template>

            <template v-if="isPDF(previewUrl)">
                <iframe :src="previewUrl" class="border w-full" style="height: 600px;" frameborder="0"></iframe>
            </template>

            <template v-if="isExcel(previewUrl)">
                <div class="excel-preview p-4">
                    <div v-if="Object.keys(sheets).length > 0" class="mb-4">
                        <label for="sheet-select" class="mr-2">シートを選択:</label>
                        <select id="sheet-select" v-model="selectedSheet" @change="updateExcelTable">
                            <option v-for="(sheet, sheetName) in sheets" :key="sheetName" :value="sheetName">
                                {{ sheetName }}
                            </option>
                        </select>
                    </div>
                    <!-- 横スクロールを有効化するためのコンテナ -->
                    <div id="excelTableContainer">
                        <table id="excelTable" class="border-collapse w-full">
                            <thead>
                                <tr>
                                    <th class="row-number-header"></th>
                                    <th v-for="(column, index) in excelColumns" :key="index" class="column-header">
                                        {{ column }}
                                        <div class="resize-handle-horizontal"></div>
                                    </th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr v-for="(row, rowIndex) in excelData" :key="rowIndex">
                                    <td class="row-number">{{ rowIndex + 1 }}</td>
                                    <td v-for="(cell, cellIndex) in row" :key="cellIndex" class="cell">
                                        {{ cell }}
                                        <div class="resize-handle-vertical"></div>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </template>

            <button @click="closePreview" class="block mt-2 bg-red-500 text-white px-4 py-2">
                クローズ
            </button>
        </div>

        <!-- 名前変更モーダル -->
        <div v-if="showRenameModal" class="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50">
            <div class="bg-white p-6 rounded shadow-md">
                <h2 class="text-xl font-bold mb-4">リネーム {{ renameType === 'folder' ? 'フォルダ' : 'ファイル' }}</h2>
                <p>現在の名前: {{ renameOriginalName }}</p>
                <label for="new-name">新しい名前:</label>
                <input id="new-name" v-model="renameNewName" class="border p-2 mb-4 w-full"
                    placeholder="Enter new name" />
                <div class="flex justify-end">
                    <button @click="cancelRename" class="bg-gray-500 text-white px-4 py-2 mr-2">キャンセル</button>
                    <button @click="renameItem" class="bg-green-500 text-white px-4 py-2">リネーム</button>
                </div>
            </div>
        </div>

        <!-- 編集モーダル -->
        <div v-if="showEditModal" class="modal-overlay">
            <div class="edit-modal">
                <h2>{{ editFileName }} を編集</h2>
                <textarea v-model="editFileContent"></textarea>
                <div class="modal-buttons">
                    <button class="cancel-btn" @click="cancelEdit">キャンセル</button>
                    <button class="save-btn" @click="saveFile">保存</button>
                </div>
            </div>
        </div>

        <!-- 移動モーダル -->
        <div v-if="showMoveModal" class="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50">
            <div class="bg-white p-6 rounded shadow-md">
                <h2 class="text-xl font-bold mb-4">移動するファイル・フォルダ</h2>
                <p class="mb-2">ファイル・フォルダ: {{ selectedFileForMove }}</p>
                <label for="move-folder">フォルダを選択してください:</label>
                <select v-model="selectedMoveFolder" id="move-folder" class="border p-2 mb-4 w-full">
                    <option value="">ルート</option>
                    <option v-for="folder in allFolders" :key="folder" :value="folder">
                        {{ folder }}
                    </option>
                </select>
                <div class="flex justify-end">
                    <button @click="cancelMove" class="bg-gray-500 text-white px-4 py-2 mr-2">キャンセル</button>
                    <button @click="moveFile" class="bg-green-500 text-white px-4 py-2">実行</button>
                </div>
            </div>
        </div>
    </div>
</template>