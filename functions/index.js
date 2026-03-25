const { onCall, HttpsError } = require("firebase-functions/v2/https");
const { setGlobalOptions } = require("firebase-functions/v2");
const { initializeApp } = require("firebase-admin/app");
const { getAuth } = require("firebase-admin/auth");
const { getFirestore, FieldValue } = require("firebase-admin/firestore");

initializeApp();
setGlobalOptions({ region: "asia-east1", maxInstances: 10 });

const adminAuth = getAuth();
const db = getFirestore();
const adminCollection = "webAdmins";
const approvalCollection = "accessApprovals";

function requireAuth(request) {
  if (!request.auth) {
    throw new HttpsError("unauthenticated", "請先登入。");
  }
}

async function mergeCustomClaims(uid, patch) {
  const userRecord = await adminAuth.getUser(uid);
  const existingClaims = userRecord.customClaims || {};
  await adminAuth.setCustomUserClaims(uid, { ...existingClaims, ...patch });
}

async function ensureAdmin(auth) {
  const adminRef = db.collection(adminCollection).doc(auth.uid);
  const adminSnap = await adminRef.get();

  if (adminSnap.exists) {
    await mergeCustomClaims(auth.uid, { admin: true, approved: true });
    return { isAdmin: true, bootstrappedAdmin: false };
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
    await mergeCustomClaims(auth.uid, { admin: true, approved: true });

    await db.collection(approvalCollection).doc(auth.uid).set({
      email,
      displayName: auth.token.name || "",
      provider,
      status: "approved",
      approvedAt: FieldValue.serverTimestamp(),
      approvedBy: auth.uid,
      approvedByEmail: email,
      bootstrap: true,
      createdAt: FieldValue.serverTimestamp(),
      updatedAt: FieldValue.serverTimestamp()
    }, { merge: true });

    return { isAdmin: true, bootstrappedAdmin: true };
  }

  return { isAdmin: false, bootstrappedAdmin: false };
}

async function ensureApprovalRequest(auth) {
  const provider = auth.token.firebase?.sign_in_provider || "";
  const email = auth.token.email || "";
  const displayName = auth.token.name || "";
  const approvalRef = db.collection(approvalCollection).doc(auth.uid);
  const approvalSnap = await approvalRef.get();

  if (!approvalSnap.exists) {
    await approvalRef.set({
      email,
      displayName,
      provider,
      status: provider === "password" ? "approved" : "pending",
      createdAt: FieldValue.serverTimestamp(),
      updatedAt: FieldValue.serverTimestamp()
    });

    if (provider === "password") {
      await mergeCustomClaims(auth.uid, { approved: true });
      return { isApproved: true, status: "approved", createdRequest: true };
    }

    return { isApproved: false, status: "pending", createdRequest: true };
  }

  const data = approvalSnap.data() || {};
  const status = data.status || "pending";

  await approvalRef.set({
    email,
    displayName,
    provider,
    updatedAt: FieldValue.serverTimestamp()
  }, { merge: true });

  if (status === "approved") {
    await mergeCustomClaims(auth.uid, { approved: true });
    return { isApproved: true, status, createdRequest: false };
  }

  return { isApproved: false, status, createdRequest: false };
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

async function requireAdmin(auth) {
  const adminState = await ensureAdmin(auth);
  if (!adminState.isAdmin) {
    throw new HttpsError("permission-denied", "你不是管理員。");
  }
  return adminState;
}

exports.getAccessStatus = onCall(async (request) => {
  requireAuth(request);

  const adminState = await ensureAdmin(request.auth);
  if (adminState.isAdmin) {
    return {
      isAdmin: true,
      isApproved: true,
      bootstrappedAdmin: adminState.bootstrappedAdmin,
      status: "approved"
    };
  }

  const approvalState = await ensureApprovalRequest(request.auth);
  return {
    isAdmin: false,
    isApproved: approvalState.isApproved,
    bootstrappedAdmin: false,
    status: approvalState.status,
    createdRequest: approvalState.createdRequest
  };
});

exports.listPendingApprovals = onCall(async (request) => {
  requireAuth(request);
  await requireAdmin(request.auth);

  const snap = await db.collection(approvalCollection).where("status", "==", "pending").get();
  const items = snap.docs
    .map((doc) => {
      const data = doc.data() || {};
      return {
        uid: doc.id,
        email: data.email || "",
        displayName: data.displayName || "",
        provider: data.provider || "",
        createdAt: data.createdAt?.toDate?.()?.toISOString?.() || ""
      };
    })
    .sort((left, right) => left.createdAt.localeCompare(right.createdAt));

  return { items };
});

exports.approvePendingUser = onCall(async (request) => {
  requireAuth(request);
  await requireAdmin(request.auth);

  const uid = String(request.data?.uid || "").trim();
  if (!uid) {
    throw new HttpsError("invalid-argument", "缺少 uid。");
  }

  const userRecord = await adminAuth.getUser(uid).catch(() => null);
  if (!userRecord) {
    throw new HttpsError("not-found", "找不到該使用者。");
  }

  await db.collection(approvalCollection).doc(uid).set({
    email: userRecord.email || "",
    displayName: userRecord.displayName || "",
    provider: userRecord.providerData?.[0]?.providerId || "",
    status: "approved",
    approvedAt: FieldValue.serverTimestamp(),
    approvedBy: request.auth.uid,
    approvedByEmail: request.auth.token.email || "",
    updatedAt: FieldValue.serverTimestamp()
  }, { merge: true });

  await mergeCustomClaims(uid, { approved: true });

  return {
    uid,
    email: userRecord.email || ""
  };
});

exports.createAuthUser = onCall(async (request) => {
  requireAuth(request);
  await requireAdmin(request.auth);

  const { email, password, displayName } = validateCreateUserInput(request.data);

  try {
    const userRecord = await adminAuth.createUser({
      email,
      password,
      displayName: displayName || undefined
    });

    await db.collection(approvalCollection).doc(userRecord.uid).set({
      email,
      displayName: displayName || "",
      provider: "password",
      status: "approved",
      approvedAt: FieldValue.serverTimestamp(),
      approvedBy: request.auth.uid,
      approvedByEmail: request.auth.token.email || "",
      createdAt: FieldValue.serverTimestamp(),
      updatedAt: FieldValue.serverTimestamp(),
      source: "admin-created"
    });

    await mergeCustomClaims(userRecord.uid, { approved: true });

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
