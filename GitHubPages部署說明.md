# 叫料記錄 GitHub Pages 部署說明

## 1. 目前已建立的檔案

- `docs/index.html`：唯讀查詢頁
- `docs/styles.css`：版面樣式
- `docs/app.js`：Firebase Auth + Firestore 查詢邏輯
- `docs/firebase-config.js`：Firebase Web App 設定檔，現在是樣板值
- `functions/index.js`：保留的 Functions 範例
- `firebase.json`、`.firebaserc`：Firebase 部署設定
- `firestore.rules`：已核准帳號才能讀資料的 Firestore 規則

## 2. 你要在 Firebase Console 做的設定

### Authentication

1. 開啟 `Authentication`
2. 至少啟用一種登入方式：
   - `Email/Password`
   - `Google`
3. 在 `Authorized domains` 加入你的 GitHub Pages 網域
   - 例如：`你的帳號.github.io`

### Firestore Rules

你現在要的是「只有已核准帳號可看，但不能改」，專案內已提供 `firestore.rules`，核心邏輯是：

```txt
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    function isAdmin() {
      return request.auth != null &&
        exists(/databases/$(database)/documents/webAdmins/$(request.auth.uid));
    }

    match /materialOrders/{document} {
      allow read: if isAdmin() || 已核准 accessApprovals 文件存在;
      allow write: if false;
    }
  }
}
```

這樣未登入不能看，只有已核准或管理員帳號才能讀取。

## 2-1. 管理員建立帳號功能

這次已加入一個「管理員工具」區塊，功能是：

- Google 登入後會進入待審核狀態
- 管理員可看到待審核名單
- 管理員可直接在網頁核准帳號
- 核准後該帳號才可瀏覽資料

這個版本改成純前端 + Firestore rules，不再依賴 Blaze。

### 第一位管理員設定方式

這版沒有用 Cloud Functions 自動升管理員，所以第一位管理員要手動建立：

1. 先用你的 Google 帳號登入網站
2. 畫面會顯示你的使用者 UID
3. 到 Firestore Console
4. 建立集合 `webAdmins`
5. 建立文件 ID = 你的 UID
6. 文件內容可放：

```json
{
  "email": "你的 Google Email"
}
```

完成後重新登入，你就會成為管理員。

## 3. 你要改的檔案

打開 `docs/firebase-config.js`，把這些值換成 Firebase Web App 的實際設定：

```js
export const firebaseSettings = {
  config: {
    apiKey: "YOUR_API_KEY",
    authDomain: "electric-bike-workorders.firebaseapp.com",
    projectId: "electric-bike-workorders",
    storageBucket: "electric-bike-workorders.firebasestorage.app",
    messagingSenderId: "YOUR_MESSAGING_SENDER_ID",
    appId: "YOUR_APP_ID"
  },
  functionsRegion: "asia-east1",
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

## 5. 部署 Firestore rules

```bash
cd /Users/herman/FIle
firebase deploy --only firestore:rules
```

如果你要連網站一起更新：

```bash
git push origin main
```

## 6. 目前網頁功能

- Firebase 登入
- Firestore `materialOrders` 唯讀查詢
- 關鍵字搜尋
- 狀態篩選
- 預設隱藏 `已完工`
- 點擊 `查看` 可看完整欄位
- Google 登入待管理員審核
- 管理員可核准待審核帳號

## 7. 注意

這個版本故意沒有新增、修改、刪除功能。
如果之後你要我再加：

- 日期區間查詢
- 匯出 Excel / CSV
- 手機版優化
- 帳號角色權限

我可以直接在這份網頁上繼續補。
