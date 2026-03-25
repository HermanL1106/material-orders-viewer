import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.5/firebase-app.js";
import {
  getAuth,
  GoogleAuthProvider,
  onAuthStateChanged,
  signInWithEmailAndPassword,
  signInWithPopup,
  signOut
} from "https://www.gstatic.com/firebasejs/10.12.5/firebase-auth.js";
import {
  getFirestore,
  collection,
  getDocs
} from "https://www.gstatic.com/firebasejs/10.12.5/firebase-firestore.js";
import {
  getFunctions,
  httpsCallable
} from "https://www.gstatic.com/firebasejs/10.12.5/firebase-functions.js";
import { firebaseSettings } from "./firebase-config.js";

const CONTACT_STATUSES = [
  "待叫料",
  "已叫料",
  "到貨",
  "到貨已通知",
  "到貨未接",
  "已預約進廠",
  "車在廠內",
  "需追蹤",
  "已完工",
  "缺料中"
];

const DETAIL_FIELDS = [
  "日期",
  "工程師",
  "車牌號碼",
  "聯繫人",
  "電話",
  "事項",
  "估價單號",
  "料件備註",
  "是否收取訂金",
  "訂金金額",
  "聯繫狀態",
  "最後聯繫日",
  "其餘備註"
];

const SEARCH_FIELDS = [
  "日期",
  "工程師",
  "車牌號碼",
  "聯繫人",
  "電話",
  "事項",
  "估價單號",
  "聯繫狀態",
  "料件備註",
  "其餘備註"
];

const state = {
  records: [],
  filteredRecords: [],
  filterStatus: "全部",
  showCompleted: false,
  searchKeyword: "",
  isAdmin: false,
  isApproved: false,
  pendingApprovals: []
};

const elements = {
  loginPanel: document.querySelector("#login-panel"),
  appPanel: document.querySelector("#app-panel"),
  accessPanel: document.querySelector("#access-panel"),
  loginMessage: document.querySelector("#login-message"),
  authStatusPill: document.querySelector("#auth-status-pill"),
  signOutButton: document.querySelector("#sign-out-button"),
  emailLoginForm: document.querySelector("#email-login-form"),
  emailInput: document.querySelector("#email-input"),
  passwordInput: document.querySelector("#password-input"),
  googleLoginButton: document.querySelector("#google-login-button"),
  adminPanel: document.querySelector("#admin-panel"),
  adminMessage: document.querySelector("#admin-message"),
  adminCreateUserForm: document.querySelector("#admin-create-user-form"),
  adminEmailInput: document.querySelector("#admin-email-input"),
  adminPasswordInput: document.querySelector("#admin-password-input"),
  adminDisplayNameInput: document.querySelector("#admin-display-name-input"),
  adminCreateUserButton: document.querySelector("#admin-create-user-button"),
  approvalRefreshButton: document.querySelector("#approval-refresh-button"),
  approvalList: document.querySelector("#approval-list"),
  toolbar: document.querySelector("#toolbar"),
  searchInput: document.querySelector("#search-input"),
  statusFilter: document.querySelector("#status-filter"),
  showCompleted: document.querySelector("#show-completed"),
  refreshButton: document.querySelector("#refresh-button"),
  summaryGrid: document.querySelector("#summary-grid"),
  totalCount: document.querySelector("#total-count"),
  visibleCount: document.querySelector("#visible-count"),
  statusSummary: document.querySelector("#status-summary"),
  tableMeta: document.querySelector("#table-meta"),
  tableShell: document.querySelector("#table-shell"),
  dataStatus: document.querySelector("#data-status"),
  recordsBody: document.querySelector("#records-body"),
  detailDialog: document.querySelector("#detail-dialog"),
  detailTitle: document.querySelector("#detail-title"),
  detailGrid: document.querySelector("#detail-grid")
};

let auth;
let db;
let functions;

function hasMissingConfig() {
  const { config } = firebaseSettings;
  return ["apiKey", "projectId", "messagingSenderId", "appId"].some((key) => {
    const value = String(config[key] ?? "").trim();
    return !value || value.includes("YOUR_");
  });
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function getDepositLabel(record) {
  const method = record["是否收取訂金"] ?? "";
  const amount = record["訂金金額"] ?? "";
  return `${method} ${amount}`.trim() || "無";
}

function compareDateDesc(left, right) {
  const leftValue = left["日期"] ?? "";
  const rightValue = right["日期"] ?? "";
  return rightValue.localeCompare(leftValue);
}

function setLoginMessage(message, isError = false) {
  elements.loginMessage.textContent = message;
  elements.loginMessage.style.background = isError ? "rgba(168, 46, 46, 0.12)" : "";
  elements.loginMessage.style.color = isError ? "#8a2222" : "";
}

function setAdminMessage(message, isError = false) {
  if (!message) {
    elements.adminMessage.classList.add("hidden");
    elements.adminMessage.textContent = "";
    return;
  }

  elements.adminMessage.classList.remove("hidden");
  elements.adminMessage.textContent = message;
  elements.adminMessage.style.background = isError ? "rgba(168, 46, 46, 0.12)" : "";
  elements.adminMessage.style.color = isError ? "#8a2222" : "";
}

function setAccessMessage(message, isError = false) {
  if (!message) {
    elements.accessPanel.classList.add("hidden");
    elements.accessPanel.textContent = "";
    return;
  }

  elements.accessPanel.classList.remove("hidden");
  elements.accessPanel.textContent = message;
  elements.accessPanel.style.background = isError ? "rgba(168, 46, 46, 0.12)" : "";
  elements.accessPanel.style.color = isError ? "#8a2222" : "";
}

function setDataStatus(message) {
  elements.dataStatus.textContent = message;
}

function getAuthErrorMessage(error) {
  const code = error?.code || "";

  if (code === "auth/invalid-credential" || code === "auth/invalid-login-credentials") {
    return "帳號或密碼錯誤，或這個 Email 尚未建立。";
  }

  if (code === "auth/user-disabled") {
    return "這個帳號已被停用。";
  }

  if (code === "auth/too-many-requests") {
    return "嘗試次數過多，請稍後再試。";
  }

  if (code === "auth/network-request-failed") {
    return "網路連線失敗，請稍後再試。";
  }

  if (code === "auth/unauthorized-domain") {
    return "目前網域未加入 Firebase Authorized domains。";
  }

  if (code === "auth/popup-closed-by-user") {
    return "登入視窗已被關閉。";
  }

  return error?.message || "登入失敗，請稍後再試。";
}

function getFunctionErrorMessage(error) {
  const code = error?.code || "";

  if (code.includes("permission-denied")) {
    return "你沒有管理員權限。";
  }

  if (code.includes("already-exists")) {
    return "這個 Email 已存在。";
  }

  if (code.includes("invalid-argument")) {
    return "資料格式不正確，請確認 Email 與密碼。";
  }

  if (code.includes("unauthenticated")) {
    return "請先登入後再操作。";
  }

  if (code.includes("unavailable") || code.includes("not-found")) {
    return "管理功能尚未部署完成，請先部署 Firebase Cloud Functions。";
  }

  return error?.message || "操作失敗，請稍後再試。";
}

function setViewerEnabled(enabled) {
  const method = enabled ? "remove" : "add";
  elements.toolbar.classList[method]("hidden");
  elements.summaryGrid.classList[method]("hidden");
  elements.tableMeta.classList[method]("hidden");
  elements.tableShell.classList[method]("hidden");
}

function populateStatusFilter() {
  elements.statusFilter.innerHTML = ["全部", ...CONTACT_STATUSES]
    .map((status) => `<option value="${status}">${status}</option>`)
    .join("");
}

function updateStats() {
  const counts = {};
  for (const record of state.records) {
    const status = record["聯繫狀態"] || "未分類";
    counts[status] = (counts[status] || 0) + 1;
  }

  elements.totalCount.textContent = String(state.records.length);
  elements.visibleCount.textContent = String(state.filteredRecords.length);

  const summary = Object.entries(counts)
    .sort((a, b) => a[0].localeCompare(b[0], "zh-Hant"))
    .map(([status, count]) => `${status} ${count} 筆`)
    .join(" / ");

  elements.statusSummary.textContent = summary || "目前沒有資料";
}

function renderEmpty(message) {
  elements.recordsBody.innerHTML = `
    <tr>
      <td colspan="14" class="empty-state">${escapeHtml(message)}</td>
    </tr>
  `;
}

function renderTable() {
  if (!state.filteredRecords.length) {
    renderEmpty("查無符合條件的資料");
    return;
  }

  elements.recordsBody.innerHTML = state.filteredRecords
    .map((record, index) => `
      <tr>
        <td>${index + 1}</td>
        <td>${escapeHtml(record["日期"] || "")}</td>
        <td>${escapeHtml(record["工程師"] || "")}</td>
        <td>${escapeHtml(record["車牌號碼"] || "")}</td>
        <td>${escapeHtml(record["聯繫人"] || "")}</td>
        <td>${escapeHtml(record["電話"] || "")}</td>
        <td>${escapeHtml(record["事項"] || "")}</td>
        <td>${escapeHtml(record["估價單號"] || "")}</td>
        <td>${escapeHtml(getDepositLabel(record))}</td>
        <td><span class="cell-status">${escapeHtml(record["聯繫狀態"] || "")}</span></td>
        <td>${escapeHtml(record["最後聯繫日"] || "")}</td>
        <td class="cell-note">${escapeHtml(record["料件備註"] || "")}</td>
        <td class="cell-note">${escapeHtml(record["其餘備註"] || "")}</td>
        <td><button class="table-button" type="button" data-record-id="${escapeHtml(record.id)}">查看</button></td>
      </tr>
    `)
    .join("");
}

function renderPendingApprovals() {
  if (!state.pendingApprovals.length) {
    elements.approvalList.innerHTML = '<div class="empty-state">目前沒有待審核帳號</div>';
    return;
  }

  elements.approvalList.innerHTML = state.pendingApprovals
    .map((item) => `
      <article class="approval-card">
        <div>
          <strong>${escapeHtml(item.email || "未提供 Email")}</strong>
          <p class="approval-meta">
            ${escapeHtml(item.displayName || "未填顯示名稱")}<br>
            登入方式：${escapeHtml(item.provider || "未知")}<br>
            UID：${escapeHtml(item.uid || "")}
          </p>
        </div>
        <div class="approval-actions">
          <button class="primary-button" type="button" data-approve-uid="${escapeHtml(item.uid || "")}">核准</button>
        </div>
      </article>
    `)
    .join("");
}

function applyFilters() {
  let nextRecords = [...state.records];

  if (state.filterStatus === "全部") {
    if (!state.showCompleted) {
      nextRecords = nextRecords.filter((record) => record["聯繫狀態"] !== "已完工");
    }
  } else {
    nextRecords = nextRecords.filter((record) => record["聯繫狀態"] === state.filterStatus);
  }

  if (state.searchKeyword) {
    const keyword = state.searchKeyword.toLowerCase();
    nextRecords = nextRecords.filter((record) =>
      SEARCH_FIELDS.some((field) =>
        String(record[field] ?? "").toLowerCase().includes(keyword)
      )
    );
  }

  state.filteredRecords = nextRecords.sort(compareDateDesc);
  updateStats();
  renderTable();
  setDataStatus(`已載入 ${state.records.length} 筆，顯示 ${state.filteredRecords.length} 筆`);
}

function openDetail(recordId) {
  const record = state.records.find((item) => item.id === recordId);
  if (!record) {
    return;
  }

  elements.detailTitle.textContent = `${record["車牌號碼"] || "未填車牌"} / ${record["聯繫人"] || "未填聯繫人"}`;
  elements.detailGrid.innerHTML = DETAIL_FIELDS
    .map((field) => `
      <dl class="detail-item">
        <dt>${escapeHtml(field)}</dt>
        <dd>${escapeHtml(record[field] || "")}</dd>
      </dl>
    `)
    .join("");

  elements.detailDialog.showModal();
}

async function loadRecords() {
  setDataStatus("資料讀取中...");
  renderEmpty("資料讀取中...");

  try {
    const snapshot = await getDocs(collection(db, firebaseSettings.collectionName));
    state.records = snapshot.docs
      .map((docSnapshot) => ({ id: docSnapshot.id, ...docSnapshot.data() }))
      .sort(compareDateDesc);
    applyFilters();
  } catch (error) {
    console.error(error);
    state.records = [];
    updateStats();
    renderEmpty("讀取失敗，請檢查 Firestore 權限或網路狀態");
    setDataStatus("讀取失敗");
  }
}

async function refreshPendingApprovals() {
  if (!state.isAdmin || !functions) {
    return;
  }

  try {
    const listPendingApprovals = httpsCallable(functions, "listPendingApprovals");
    const result = await listPendingApprovals();
    state.pendingApprovals = Array.isArray(result.data?.items) ? result.data.items : [];
    renderPendingApprovals();
  } catch (error) {
    console.error(error);
    setAdminMessage(`待審核名單讀取失敗：${getFunctionErrorMessage(error)}`, true);
  }
}

async function resolveAccessStatus() {
  state.isAdmin = false;
  state.isApproved = false;
  state.pendingApprovals = [];
  elements.adminPanel.classList.add("hidden");
  setViewerEnabled(false);
  renderEmpty("權限確認中...");
  setAdminMessage("");
  setAccessMessage("");

  if (!functions) {
    return false;
  }

  try {
    const getAccessStatus = httpsCallable(functions, "getAccessStatus");
    const result = await getAccessStatus();
    state.isAdmin = Boolean(result.data?.isAdmin);
    state.isApproved = Boolean(result.data?.isApproved || state.isAdmin);

    if (state.isAdmin) {
      elements.adminPanel.classList.remove("hidden");
      await auth.currentUser?.getIdToken(true);
      await refreshPendingApprovals();

      if (result.data?.bootstrappedAdmin) {
        setAdminMessage("你已成為第一位管理員，並已自動核准。現在可以審核其他 Google 使用者。");
      } else {
        setAdminMessage("你是管理員，可核准 Google 登入使用者並建立 Email/Password 帳號。");
      }

      setViewerEnabled(true);
      return true;
    }

    if (state.isApproved) {
      await auth.currentUser?.getIdToken(true);
      setViewerEnabled(true);
      setAccessMessage("帳號已核准，可瀏覽資料。");
      return true;
    }

    setViewerEnabled(false);
    setAccessMessage("你的 Google 帳號已送出審核，請等待管理員核准後再重新登入。");
    setDataStatus("帳號待審核");
    renderEmpty("帳號待審核中，管理員核准後才能瀏覽資料");
    return false;
  } catch (error) {
    console.error(error);
    setViewerEnabled(false);
    setAccessMessage(`權限確認失敗：${getFunctionErrorMessage(error)}`, true);
    setDataStatus("權限確認失敗");
    renderEmpty("無法確認帳號權限");
    return false;
  }
}

async function handleEmailLogin(event) {
  event.preventDefault();
  const email = elements.emailInput.value.trim();
  const password = elements.passwordInput.value;

  if (!email || !password) {
    setLoginMessage("請輸入 Email 與 Password。", true);
    return;
  }

  try {
    setLoginMessage("登入中...");
    await signInWithEmailAndPassword(auth, email, password);
    setLoginMessage("登入成功。");
    elements.passwordInput.value = "";
  } catch (error) {
    console.error(error);
    setLoginMessage(`登入失敗：${getAuthErrorMessage(error)}`, true);
  }
}

async function handleGoogleLogin() {
  try {
    setLoginMessage("Google 登入中...");
    await signInWithPopup(auth, new GoogleAuthProvider());
    setLoginMessage("Google 登入成功。");
  } catch (error) {
    console.error(error);
    setLoginMessage(`Google 登入失敗：${getAuthErrorMessage(error)}`, true);
  }
}

async function handleSignOut() {
  try {
    await signOut(auth);
  } catch (error) {
    console.error(error);
    setLoginMessage(`登出失敗：${error.message}`, true);
  }
}

async function handleAuthState(user) {
  if (!user) {
    elements.loginPanel.classList.remove("hidden");
    elements.appPanel.classList.add("hidden");
    elements.adminPanel.classList.add("hidden");
    elements.signOutButton.classList.add("hidden");
    elements.authStatusPill.textContent = "未登入";
    setLoginMessage("請輸入已建立的 Firebase 帳號密碼登入。");
    setAdminMessage("");
    setAccessMessage("");
    setViewerEnabled(false);
    renderEmpty("尚未登入");
    setDataStatus("等待登入後載入資料");
    return;
  }

  elements.loginPanel.classList.add("hidden");
  elements.appPanel.classList.remove("hidden");
  elements.signOutButton.classList.remove("hidden");
  elements.authStatusPill.textContent = `${user.email || user.displayName || "已登入"}`;
  const canRead = await resolveAccessStatus();
  if (canRead) {
    loadRecords();
  }
}

async function handleCreateUser(event) {
  event.preventDefault();

  const email = elements.adminEmailInput.value.trim();
  const password = elements.adminPasswordInput.value.trim();
  const displayName = elements.adminDisplayNameInput.value.trim();

  if (!email || !password) {
    setAdminMessage("請輸入 Email 與密碼。", true);
    return;
  }

  if (password.length < 6) {
    setAdminMessage("密碼至少需要 6 碼。", true);
    return;
  }

  try {
    setAdminMessage("建立帳號中...");
    elements.adminCreateUserButton.disabled = true;

    const createAuthUser = httpsCallable(functions, "createAuthUser");
    const result = await createAuthUser({ email, password, displayName });
    const createdEmail = result.data?.email || email;

    setAdminMessage(`建立成功：${createdEmail}`);
    elements.adminCreateUserForm.reset();
  } catch (error) {
    console.error(error);
    setAdminMessage(`建立失敗：${getFunctionErrorMessage(error)}`, true);
  } finally {
    elements.adminCreateUserButton.disabled = false;
  }
}

async function handleApproveUser(uid) {
  if (!uid) {
    return;
  }

  try {
    setAdminMessage("核准中...");
    const approvePendingUser = httpsCallable(functions, "approvePendingUser");
    const result = await approvePendingUser({ uid });
    setAdminMessage(`已核准：${result.data?.email || uid}`);
    await refreshPendingApprovals();
  } catch (error) {
    console.error(error);
    setAdminMessage(`核准失敗：${getFunctionErrorMessage(error)}`, true);
  }
}

function bindEvents() {
  elements.emailLoginForm.addEventListener("submit", handleEmailLogin);
  elements.googleLoginButton.addEventListener("click", handleGoogleLogin);
  elements.signOutButton.addEventListener("click", handleSignOut);
  elements.adminCreateUserForm.addEventListener("submit", handleCreateUser);
  elements.approvalRefreshButton.addEventListener("click", refreshPendingApprovals);

  elements.searchInput.addEventListener("input", (event) => {
    state.searchKeyword = event.target.value.trim();
    applyFilters();
  });

  elements.statusFilter.addEventListener("change", (event) => {
    state.filterStatus = event.target.value;
    applyFilters();
  });

  elements.showCompleted.addEventListener("change", (event) => {
    state.showCompleted = event.target.checked;
    applyFilters();
  });

  elements.refreshButton.addEventListener("click", loadRecords);

  elements.recordsBody.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) {
      return;
    }

    const recordId = target.getAttribute("data-record-id");
    if (recordId) {
      openDetail(recordId);
    }
  });

  elements.approvalList.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) {
      return;
    }

    const uid = target.getAttribute("data-approve-uid");
    if (uid) {
      handleApproveUser(uid);
    }
  });
}

function boot() {
  populateStatusFilter();
  bindEvents();

  if (hasMissingConfig()) {
    setLoginMessage(
      "請先編輯 docs/firebase-config.js，至少填入 apiKey、messagingSenderId、appId。",
      true
    );
    elements.googleLoginButton.disabled = true;
    elements.emailLoginForm.querySelector("button").disabled = true;
    return;
  }

  try {
    const normalizedConfig = {
      ...firebaseSettings.config,
      authDomain: firebaseSettings.config.authDomain || `${firebaseSettings.config.projectId}.firebaseapp.com`,
      storageBucket: firebaseSettings.config.storageBucket || `${firebaseSettings.config.projectId}.appspot.com`
    };

    const app = initializeApp(normalizedConfig);
    auth = getAuth(app);
    db = getFirestore(app);
    functions = getFunctions(app, firebaseSettings.functionsRegion || "asia-east1");

    if (!firebaseSettings.authProviders.google) {
      elements.googleLoginButton.classList.add("hidden");
    }

    if (!firebaseSettings.authProviders.emailPassword) {
      elements.emailLoginForm.classList.add("hidden");
    }

    onAuthStateChanged(auth, handleAuthState);
  } catch (error) {
    console.error(error);
    setLoginMessage(`Firebase 初始化失敗：${error.message}`, true);
    elements.googleLoginButton.disabled = true;
    elements.emailLoginForm.querySelector("button").disabled = true;
  }
}

boot();
