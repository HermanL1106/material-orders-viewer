const projectId = "electric-bike-workorders";

export const firebaseSettings = {
  config: {
    apiKey: "AIzaSyCJRG7xReo0_dx-ZaJhaUVIEU58JifmVAk",
    messagingSenderId: "41212869744",
    appId: "1:41212869744:web:be69af07e77e816efb88b5",
    measurementId: "G-V3VTZZ0T59",

    authDomain: `${projectId}.firebaseapp.com`,
    projectId,
    storageBucket: "electric-bike-workorders.firebasestorage.app"
  },
  collectionName: "materialOrders",
  authProviders: {
    emailPassword: true,
    google: true
  }
};
