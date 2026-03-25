const projectId = "electric-bike-workorders";

export const firebaseSettings = {
  config: {
    // 這三個值無法從目前資料夾內的 Python 程式推回來，需到 Firebase Console > Project settings > Your apps 複製
    apiKey: "",
    messagingSenderId: "",
    appId: "",

    // 這些值可依現有專案 ID 推得
    authDomain: `${projectId}.firebaseapp.com`,
    projectId,
    storageBucket: `${projectId}.appspot.com`
  },
  collectionName: "materialOrders",
  authProviders: {
    emailPassword: true,
    google: true
  }
};
