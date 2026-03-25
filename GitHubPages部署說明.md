# 叫料記錄 GitHub Pages 部署說明

## 1. 目前已建立的檔案

- `docs/index.html`：唯讀查詢頁
- `docs/styles.css`：版面樣式
- `docs/app.js`：Firebase Auth + Firestore 查詢邏輯
- `docs/firebase-config.js`：Firebase Web App 設定檔，現在是樣板值
- `functions/index.js`：管理員建立帳號、Google 待審核、核准權限的 Cloud Functions
- `firebase.json`、`.firebaserc`：Firebase 部署設定

## 2. 你要在 Firebase Console 做的設定

### Authentication

1. 開啟 `Authentication`
2. 至少啟用一種登入方式：
   - `Email/Password`
   - `Google`
3. 在 `Authorized domains` 加入你的 GitHub Pages 網域
   - 例如：`你的帳號.github.io`

### Firestore Rules

你現在要的是「只有已核准帳號可看，但不能改」，可以把規則改成：

```txt
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /materialOrders/{document} {
      allow read: if request.auth != null
                  && (request.auth.token.approved == true
                      || request.auth.token.admin == true);
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
- 管理員核准後，該帳號才可瀏覽資料
- 管理員可在網頁直接建立新的 Email/Password 帳號

注意：

- 這個功能不是純 GitHub Pages 前端完成
- 它需要另外部署 Firebase Cloud Functions

### 第一位管理員規則

目前程式設計是：

- `webAdmins` 集合裡如果還沒有任何管理員
- 第一個成功用 Google 登入並呼叫管理功能的人
- 會自動成為第一位管理員

之後只有已在 `webAdmins` 裡的使用者，才能繼續建立帳號與審核其他 Google 使用者。

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

## 5. Cloud Functions 部署方式

你的電腦要先安裝 Firebase CLI：

```bash
npm install -g firebase-tools
```

登入：

```bash
firebase login
```

在專案目錄部署 Functions：

```bash
cd /Users/herman/FIle
firebase deploy --only functions
```

部署完成後，GitHub Pages 前端就能呼叫：

- `getAccessStatus`
- `listPendingApprovals`
- `approvePendingUser`
- `createAuthUser`

## 6. 目前網頁功能

- Firebase 登入
- Firestore `materialOrders` 唯讀查詢
- 關鍵字搜尋
- 狀態篩選
- 預設隱藏 `已完工`
- 點擊 `查看` 可看完整欄位
- Google 登入待管理員審核
- 管理員可核准待審核帳號
- 管理員可建立新的 Email/Password 帳號

## 7. 注意

這個版本故意沒有新增、修改、刪除功能。
如果之後你要我再加：

- 日期區間查詢
- 匯出 Excel / CSV
- 手機版優化
- 帳號角色權限

我可以直接在這份網頁上繼續補。
