const { onCall, HttpsError } = require("firebase-functions/v2/https");
const { setGlobalOptions } = require("firebase-functions/v2");
const { initializeApp } = require("firebase-admin/app");
const { getAuth } = require("firebase-admin/auth");
const { getFirestore, FieldValue } = require("firebase-admin/firestore");

initializeApp();
setGlobalOptions({ region: "asia-east1", maxInstances: 10 });

const db = getFirestore();
const adminCollection = "webAdmins";

function requireAuth(request) {
  if (!request.auth) {
    throw new HttpsError("unauthenticated", "請先登入。");
  }
}

async function ensureAdmin(auth) {
  const adminRef = db.collection(adminCollection).doc(auth.uid);
  const adminSnap = await adminRef.get();

  if (adminSnap.exists) {
    return { isAdmin: true, bootstrapped: false };
  }

  const provider = auth.token.firebase?.sign_in_provider;
  const email = auth.token.email || "";
  const verified = Boolean(auth.token.email_verified);
  const firstAdminSnap = await db.collection(adminCollection).limit(1).get();

  if (firstAdminSnap.empty && provider === "google.com" && verified) {
    await adminRef.create({
      email,
      createdAt: FieldValue.serverTimestamp(),
      bootstrap: true
    });

    return { isAdmin: true, bootstrapped: true };
  }

  return { isAdmin: false, bootstrapped: false };
}

function validateCreateUserInput(data) {
  const email = String(data?.email || "").trim();
  const password = String(data?.password || "").trim();
  const displayName = String(data?.displayName || "").trim();

  if (!email || !email.includes("@")) {
    throw new HttpsError("invalid-argument", "Email 格式不正確。");
  }

  if (password.length < 6) {
    throw new HttpsError("invalid-argument", "密碼至少需要 6 碼。");
  }

  return { email, password, displayName };
}

exports.getAdminStatus = onCall(async (request) => {
  requireAuth(request);

  const result = await ensureAdmin(request.auth);
  return {
    isAdmin: result.isAdmin,
    bootstrapped: result.bootstrapped,
    email: request.auth.token.email || ""
  };
});

exports.createAuthUser = onCall(async (request) => {
  requireAuth(request);

  const adminState = await ensureAdmin(request.auth);
  if (!adminState.isAdmin) {
    throw new HttpsError("permission-denied", "你不是管理員。");
  }

  const { email, password, displayName } = validateCreateUserInput(request.data);

  try {
    const userRecord = await getAuth().createUser({
      email,
      password,
      displayName: displayName || undefined
    });

    return {
      uid: userRecord.uid,
      email: userRecord.email || email,
      displayName: userRecord.displayName || displayName || ""
    };
  } catch (error) {
    if (error.code === "auth/email-already-exists") {
      throw new HttpsError("already-exists", "這個 Email 已存在。");
    }

    if (error.code === "auth/invalid-password" || error.code === "auth/invalid-email") {
      throw new HttpsError("invalid-argument", error.message);
    }

    console.error(error);
    throw new HttpsError("internal", error.message || "建立帳號失敗。");
  }
});
