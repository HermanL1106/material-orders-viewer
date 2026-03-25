# 叫料記錄 GitHub Pages 部署說明

## 1. 目前已建立的檔案

- `docs/index.html`：唯讀查詢頁
- `docs/styles.css`：版面樣式
- `docs/app.js`：Firebase Auth + Firestore 查詢邏輯
- `docs/firebase-config.js`：Firebase Web App 設定檔，現在是樣板值

## 2. 你要在 Firebase Console 做的設定

### Authentication

1. 開啟 `Authentication`
2. 至少啟用一種登入方式：
   - `Email/Password`
   - `Google`
3. 在 `Authorized domains` 加入你的 GitHub Pages 網域
   - 例如：`你的帳號.github.io`

### Firestore Rules

你現在要的是「登入後可看，但不能改」，可以把規則改成：

```txt
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /materialOrders/{document} {
      allow read: if request.auth != null;
      allow write: if false;
    }
  }
}
```

這樣未登入不能看，已登入只能讀取。

## 3. 你要改的檔案

打開 `docs/firebase-config.js`，把這些值換成 Firebase Web App 的實際設定：

```js
export const firebaseSettings = {
  config: {
    apiKey: "YOUR_API_KEY",
    authDomain: "YOUR_PROJECT.firebaseapp.com",
    projectId: "electric-bike-workorders",
    storageBucket: "YOUR_PROJECT.appspot.com",
    messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
    appId: "YOUR_APP_ID"
  },
  collectionName: "materialOrders",
  authProviders: {
    emailPassword: true,
    google: true
  }
};
```

`projectId` 我已先填成你 Python 程式裡的 `electric-bike-workorders`。

## 4. GitHub Pages 發布方式

把整個資料夾放到 GitHub Repo 後：

1. 到 GitHub Repo 的 `Settings`
2. 打開 `Pages`
3. Source 選 `Deploy from a branch`
4. Branch 選你的主分支
5. Folder 選 `/docs`

完成後 GitHub 會給你一個網址。

## 5. 目前網頁功能

- Firebase 登入
- Firestore `materialOrders` 唯讀查詢
- 關鍵字搜尋
- 狀態篩選
- 預設隱藏 `已完工`
- 點擊 `查看` 可看完整欄位

## 6. 注意

這個版本故意沒有新增、修改、刪除功能。
如果之後你要我再加：

- 日期區間查詢
- 匯出 Excel / CSV
- 手機版優化
- 帳號角色權限

我可以直接在這份網頁上繼續補。
