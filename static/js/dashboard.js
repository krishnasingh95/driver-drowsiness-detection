/**
 * DrowsyGuard AI – Multi-Screen Dashboard & Dual Audio Controller
 * B.Tech AI/ML Mini Project
 */

// ── GLOBAL APPLICATION STATE ──────────────────────────────
let isTestAudioPlaying = false;
let isAudioMuted       = false;
let isAudioUnlocked    = false;
let currentScreen      = "screen-cockpit";

let earChartInstance   = null;
let marChartInstance   = null;
let telemetryLabels    = [];
let earChartData       = [];
let marChartData       = [];

const browserAudio     = document.getElementById("browserAudio");

// ══════════════════════════════════════════════════════════
//  1. MULTI-SCREEN NAVIGATION ENGINE
// ══════════════════════════════════════════════════════════
const screenTitles = {
  "screen-cockpit":     { title: "Live Cockpit Monitor",         crumb: "Safety Cockpit • Real-time Camera" },
  "screen-calibration": { title: "Eye Calibration Studio",       crumb: "Biometric Setup • Personalized Thresholds" },
  "screen-simulator":   { title: "AI Lab & Driver Simulator",    crumb: "Random Forest Classifier • What-If Testing" },
  "screen-telemetry":   { title: "Live Telemetry & Analytics",    crumb: "Real-time Biometrics • Continuous Charts" },
  "screen-logs":        { title: "Incident History & Audit Log", crumb: "Safety Records • Event CSV Export" },
  "screen-viva":        { title: "Viva & Architecture Hub",      crumb: "System Design • Top 10 Viva Q&A" },
};

function initNavigation() {
  const navBtns = document.querySelectorAll(".nav-btn");
  navBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetScreen = btn.getAttribute("data-screen");
      if (!targetScreen) return;

      // Update Sidebar Active state
      navBtns.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");

      // Switch Visible Screen
      document.querySelectorAll(".screen").forEach((sc) => sc.classList.remove("active"));
      const screenElem = document.getElementById(targetScreen);
      if (screenElem) screenElem.classList.add("active");

      currentScreen = targetScreen;

      // Update Header Text
      if (screenTitles[targetScreen]) {
        document.getElementById("currentScreenTitle").textContent = screenTitles[targetScreen].title;
        document.getElementById("headerBreadcrumb").textContent   = screenTitles[targetScreen].crumb;
      }

      // Screen-specific triggers
      if (targetScreen === "screen-logs") {
        fetchLogsTable();
      } else if (targetScreen === "screen-simulator") {
        runSimulation();
      }
    });
  });
}

// ══════════════════════════════════════════════════════════
//  2. DUAL AUDIO CONTROLLER (funny_munni.mp3)
// ══════════════════════════════════════════════════════════
function unlockAudioEngine() {
  if (isAudioUnlocked) return;
  // Play silent or quick touch to satisfy browser autoplay policy
  browserAudio.play().then(() => {
    browserAudio.pause();
    browserAudio.currentTime = 0;
    isAudioUnlocked = true;
  }).catch(() => {});
}
document.addEventListener("click", unlockAudioEngine, { once: true });
document.addEventListener("keydown", unlockAudioEngine, { once: true });

async function toggleTestAudio() {
  unlockAudioEngine();

  if (!isTestAudioPlaying) {
    // Start playback (Both Hardware Pygame on PC and HTML5 in Browser)
    try {
      await fetch("/api/test_sound_on", { method: "POST" });
    } catch (e) {}

    browserAudio.currentTime = 0;
    browserAudio.play().catch(() => {});
    isTestAudioPlaying = true;
    updateAudioButtonsUI(true);
  } else {
    // Stop playback
    try {
      await fetch("/api/test_sound_off", { method: "POST" });
    } catch (e) {}

    browserAudio.pause();
    browserAudio.currentTime = 0;
    isTestAudioPlaying = false;
    updateAudioButtonsUI(false);
  }
}

function updateAudioButtonsUI(playing) {
  const sidebarBtn = document.getElementById("sidebarTestBtn");
  const headerBtnText = document.getElementById("headerSoundText");
  const cockpitBtn = document.getElementById("cockpitTestSongBtn");
  const songDot = document.getElementById("songPlayingDot");
  const songTitle = document.getElementById("songStatusTitle");

  if (playing) {
    if (sidebarBtn) sidebarBtn.innerHTML = "⏹ Stop Alert Song";
    if (headerBtnText) headerBtnText.textContent = "Stop Song";
    if (cockpitBtn) cockpitBtn.textContent = "⏹ Stop Song";
    if (songDot) songDot.classList.add("active");
    if (songTitle) songTitle.textContent = "Song Playing (funny_munni.mp3)";
  } else {
    if (sidebarBtn) sidebarBtn.innerHTML = "▶ Test Alert Song";
    if (headerBtnText) headerBtnText.textContent = "Test Song";
    if (cockpitBtn) cockpitBtn.textContent = "▶ Play Song";
    if (songDot) songDot.classList.remove("active");
    if (songTitle) songTitle.textContent = "Song Alert Ready";
  }
}

async function toggleMute() {
  try {
    const res = await fetch("/api/toggle_audio", { method: "POST" });
    const data = await res.json();
    isAudioMuted = !data.audio_enabled;

    browserAudio.muted = isAudioMuted;
    document.getElementById("muteIcon").textContent = isAudioMuted ? "🔇" : "🔊";
    const hwTag = document.getElementById("hwSoundTag");
    if (hwTag) {
      hwTag.textContent = isAudioMuted ? "🔇 Sound Muted" : "🔊 Song Armed";
      hwTag.style.borderColor = isAudioMuted ? "var(--red)" : "var(--amber)";
    }
  } catch (e) {
    console.error("Toggle mute failed:", e);
  }
}

function dismissEmergency() {
  document.getElementById("emergencyBanner").style.display = "none";
}

// ══════════════════════════════════════════════════════════
//  3. TELEMETRY POLLING & UI UPDATER
// ══════════════════════════════════════════════════════════
let prevRisk = "NORMAL";

async function pollTelemetryState() {
  try {
    const res = await fetch("/api/state");
    const data = await res.json();

    // ── A. Handle Audio Synchronization ──────────────────
    if (data.play_alert && !isAudioMuted) {
      if (browserAudio.paused) {
        browserAudio.play().catch(() => {});
      }
      updateAudioButtonsUI(true);
      document.getElementById("emergencyBanner").style.display = "flex";
    } else if (!data.play_alert && !isTestAudioPlaying) {
      if (!browserAudio.paused) {
        browserAudio.pause();
        browserAudio.currentTime = 0;
      }
      updateAudioButtonsUI(false);
      document.getElementById("emergencyBanner").style.display = "none";
    }

    // ── B. Cockpit Screen Updates ─────────────────────────
    updateCockpitUI(data);

    // ── C. Calibration Screen Updates ─────────────────────
    updateCalibrationUI(data);

    // ── D. Telemetry Charts Updates ───────────────────────
    updateTelemetryCharts(data);

  } catch (err) {
    console.error("Poll telemetry error:", err);
  }
}

function updateCockpitUI(data) {
  // 1. Risk Level Master Badge & Stepper
  const risk = data.risk_level || "NORMAL";
  const masterCard = document.getElementById("riskMasterCard");
  const topPill = document.getElementById("topRiskPill");
  const topRiskText = document.getElementById("topRiskText");
  const badgeText = document.getElementById("riskBadgeText");
  const centerIcon = document.getElementById("riskCenterIcon");
  const mainHead = document.getElementById("riskMainHeading");
  const desc = document.getElementById("riskDescription");

  // Reset classes
  masterCard.className = `panel risk-card ${risk.toLowerCase()}`;
  topPill.className = `risk-pill ${risk.toLowerCase()}`;
  topRiskText.textContent = risk.replace("_", " ");
  badgeText.className = `risk-badge ${risk.toLowerCase()}`;
  badgeText.textContent = risk.replace("_", " ");

  document.getElementById("step1").classList.remove("active");
  document.getElementById("step2").classList.remove("active");
  document.getElementById("step3").classList.remove("active");

  if (risk === "NORMAL") {
    centerIcon.textContent = "✅";
    mainHead.textContent = "NORMAL";
    mainHead.style.color = "var(--green)";
    desc.textContent = "Driver is attentive & eyes are open naturally.";
    document.getElementById("step1").classList.add("active");
  } else if (risk === "CAUTION") {
    centerIcon.textContent = "⚠️";
    mainHead.textContent = "CAUTION";
    mainHead.style.color = "var(--amber)";
    desc.textContent = "Signs of fatigue detected (yawn or partial closure). Stay attentive!";
    document.getElementById("step1").classList.add("active");
    document.getElementById("step2").classList.add("active");
  } else if (risk === "HIGH_RISK") {
    centerIcon.textContent = "🚨";
    mainHead.textContent = "HIGH RISK";
    mainHead.style.color = "var(--red)";
    desc.textContent = "CRITICAL: Sustained eye closure detected! Alert song active!";
    document.getElementById("step1").classList.add("active");
    document.getElementById("step2").classList.add("active");
    document.getElementById("step3").classList.add("active");
  }

  // 2. ML Badge
  const mlChip = document.getElementById("cockpitMlChip");
  mlChip.textContent = data.ml_prediction;
  mlChip.className = `ml-chip ${data.ml_prediction.toLowerCase()}`;

  const confPct = Math.round((data.ml_confidence || 0.8) * 100);
  document.getElementById("cockpitMlConfidenceBar").style.width = `${confPct}%`;
  document.getElementById("cockpitMlConfText").textContent = `${confPct}%`;

  // 3. Telemetry Gauges
  const avgEar = data.avg_ear || 0.0;
  const mar = data.mar || 0.0;
  const closedSec = data.eye_closed_seconds || 0.0;
  const thresh = data.personal_threshold || 0.25;

  document.getElementById("valAvgEar").textContent = avgEar.toFixed(3);
  document.getElementById("valMar").textContent = mar.toFixed(3);
  document.getElementById("valClosedSec").textContent = `${closedSec.toFixed(1)}s`;
  document.getElementById("valThreshSub").textContent = thresh.toFixed(3);

  // Bars width
  const earPct = Math.min(Math.round((avgEar / 0.5) * 100), 100);
  const marPct = Math.min(Math.round((mar / 0.8) * 100), 100);
  const alarmDelay = data.alarm_delay || 0.5;
  const closedPct = Math.min(Math.round((closedSec / alarmDelay) * 100), 100);

  const earBar = document.getElementById("barAvgEar");
  earBar.style.width = `${earPct}%`;
  earBar.className = `gauge-bar-fill ${avgEar < thresh ? "red" : "green"}`;

  document.getElementById("barMar").style.width = `${marPct}%`;
  document.getElementById("barClosedSec").style.width = `${closedPct}%`;

  // Threshold marker line on EAR bar
  const threshPct = Math.min(Math.round((thresh / 0.5) * 100), 100);
  document.getElementById("earThreshLine").style.left = `${threshPct}%`;

  // Status tags
  const earTag = document.getElementById("earTagStatus");
  if (avgEar < thresh) {
    earTag.textContent = "Closed";
    earTag.className = "tag-status danger";
  } else {
    earTag.textContent = "Open";
    earTag.className = "tag-status";
  }

  const marTag = document.getElementById("marTagStatus");
  if (mar >= 0.62) {
    marTag.textContent = "Yawning!";
    marTag.className = "tag-status danger";
  } else {
    marTag.textContent = "Mouth Closed";
    marTag.className = "tag-status";
  }

  const closedTag = document.getElementById("closedTagStatus");
  if (closedSec >= alarmDelay) {
    closedTag.textContent = "ALARM SONG ACTIVE!";
    closedTag.className = "tag-status danger";
  } else if (closedSec > 0.1) {
    closedTag.textContent = "Closing...";
    closedTag.className = "tag-status danger";
  } else {
    closedTag.textContent = "Open";
    closedTag.className = "tag-status";
  }

  // FPS & Session
  document.getElementById("liveFps").textContent = (data.fps || 0.0).toFixed(1);
  const dur = data.session_duration || 0;
  document.getElementById("liveSessionTime").textContent = `${Math.floor(dur / 60)}m ${Math.round(dur % 60)}s`;

  // Face overlay
  const noFaceBox = document.getElementById("cockpitNoFace");
  if (noFaceBox) {
    noFaceBox.style.display = data.face_detected ? "none" : "flex";
  }

  // Sidebar alert count
  document.getElementById("sidebarAlertCount").textContent = data.total_alerts || 0;
}

function updateCalibrationUI(data) {
  const calProg = data.calibration_progress || 0;
  document.getElementById("calPercentText").textContent = `${calProg}%`;
  document.getElementById("calProgressBar").style.width = `${calProg}%`;

  const chip = document.getElementById("calStatusChip");
  const sidePill = document.getElementById("sidebarCalPill");

  if (data.calibrated) {
    if (chip) { chip.textContent = "✅ Calibrated"; chip.style.color = "var(--green)"; }
    if (sidePill) { sidePill.textContent = "Active"; sidePill.style.color = "var(--green)"; }
  } else {
    if (chip) { chip.textContent = `Calibrating ${calProg}%`; chip.style.color = "var(--amber)"; }
    if (sidePill) { sidePill.textContent = "In Progress"; sidePill.style.color = "var(--amber)"; }
  }

  document.getElementById("calBaselineEarVal").textContent = (data.baseline_ear || 0.0).toFixed(3);
  document.getElementById("calPersonalThreshVal").textContent = (data.personal_threshold || 0.25).toFixed(3);
}

// ══════════════════════════════════════════════════════════
//  4. RE-CALIBRATION API CALL
// ══════════════════════════════════════════════════════════
async function triggerRecalibrate() {
  try {
    await fetch("/api/reset_calibration", { method: "POST" });
    // Switch to calibration screen so user sees progress
    const calNavBtn = document.querySelector('[data-screen="screen-calibration"]');
    if (calNavBtn) calNavBtn.click();
  } catch (err) {
    console.error("Recalibrate failed:", err);
  }
}

// ══════════════════════════════════════════════════════════
//  5. INTERACTIVE ML SIMULATOR (SCREEN 3)
// ══════════════════════════════════════════════════════════
async function runSimulation() {
  const lEar = parseFloat(document.getElementById("simLeftEar").value);
  const rEar = parseFloat(document.getElementById("simRightEar").value);
  const mar  = parseFloat(document.getElementById("simMar").value);
  const cls  = parseFloat(document.getElementById("simClosedSec").value);

  document.getElementById("simValLeftEar").textContent = lEar.toFixed(3);
  document.getElementById("simValRightEar").textContent = rEar.toFixed(3);
  document.getElementById("simValMar").textContent = mar.toFixed(3);
  document.getElementById("simValClosedSec").textContent = `${cls.toFixed(1)}s`;

  try {
    const res = await fetch("/api/simulate_predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        left_ear: lEar,
        right_ear: rEar,
        mar: mar,
        eye_closed_seconds: cls
      })
    });
    const d = await res.json();

    const badge = document.getElementById("simRiskBadge");
    const heading = document.getElementById("simRiskHeading");
    const desc = document.getElementById("simRiskDesc");

    badge.className = `sim-res-badge ${d.risk_level === "HIGH_RISK" ? "danger" : ""}`;
    badge.textContent = d.risk_level.replace("_", " ");

    if (d.risk_level === "NORMAL") {
      heading.textContent = "NORMAL CONDITION";
      desc.textContent = "Driver is attentive and safe. No warnings needed.";
      document.getElementById("simAudioStatus").textContent = "Silent";
      document.getElementById("simAudioStatus").style.color = "var(--text-muted)";
    } else if (d.risk_level === "CAUTION") {
      heading.textContent = "CAUTION WARNING";
      desc.textContent = "Moderate fatigue detected (yawn or partial closure).";
      document.getElementById("simAudioStatus").textContent = "Silent";
      document.getElementById("simAudioStatus").style.color = "var(--amber)";
    } else {
      heading.textContent = "HIGH RISK DROWSINESS!";
      desc.textContent = "Prolonged eye closure triggers emergency alert song!";
      document.getElementById("simAudioStatus").textContent = "🎵 PLAYING";
      document.getElementById("simAudioStatus").style.color = "var(--red)";
    }

    document.getElementById("simMlClass").textContent = d.ml_prediction;
    document.getElementById("simMlClass").style.color = d.ml_prediction === "Drowsy" ? "var(--red)" : "var(--green)";
    document.getElementById("simMlConf").textContent = `${Math.round(d.ml_confidence * 100)}%`;
    document.getElementById("simAvgEar").textContent = d.avg_ear.toFixed(3);

  } catch (e) {
    console.error("Simulation error:", e);
  }
}

function resetSimulator() {
  document.getElementById("simLeftEar").value = 0.35;
  document.getElementById("simRightEar").value = 0.35;
  document.getElementById("simMar").value = 0.05;
  document.getElementById("simClosedSec").value = 0.0;
  runSimulation();
}

function setSimPreset(type) {
  if (type === "normal") {
    document.getElementById("simLeftEar").value = 0.38;
    document.getElementById("simRightEar").value = 0.38;
    document.getElementById("simMar").value = 0.05;
    document.getElementById("simClosedSec").value = 0.0;
  } else if (type === "yawn") {
    document.getElementById("simLeftEar").value = 0.30;
    document.getElementById("simRightEar").value = 0.30;
    document.getElementById("simMar").value = 0.75;
    document.getElementById("simClosedSec").value = 0.0;
  } else if (type === "blink") {
    document.getElementById("simLeftEar").value = 0.12;
    document.getElementById("simRightEar").value = 0.12;
    document.getElementById("simMar").value = 0.05;
    document.getElementById("simClosedSec").value = 0.3;
  } else if (type === "drowsy") {
    document.getElementById("simLeftEar").value = 0.11;
    document.getElementById("simRightEar").value = 0.11;
    document.getElementById("simMar").value = 0.10;
    document.getElementById("simClosedSec").value = 2.5;
  }
  runSimulation();
}

// ══════════════════════════════════════════════════════════
//  6. REAL-TIME CHARTS (SCREEN 4)
// ══════════════════════════════════════════════════════════
function initTelemetryCharts() {
  const ctxEar = document.getElementById("liveEarChart").getContext("2d");
  earChartInstance = new Chart(ctxEar, {
    type: "line",
    data: {
      labels: telemetryLabels,
      datasets: [{
        label: "Driver Average EAR",
        data: earChartData,
        borderColor: "#10b981",
        backgroundColor: "rgba(16, 185, 129, 0.08)",
        borderWidth: 2,
        tension: 0.3,
        fill: true,
        pointRadius: 0
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      scales: {
        x: { display: false },
        y: {
          min: 0.0,
          max: 0.55,
          grid: { color: "#232d3d" },
          ticks: { color: "#64748b", font: { family: "JetBrains Mono", size: 10 } }
        }
      },
      plugins: {
        legend: { display: false }
      }
    }
  });

  const ctxMar = document.getElementById("liveMarChart").getContext("2d");
  marChartInstance = new Chart(ctxMar, {
    type: "line",
    data: {
      labels: telemetryLabels,
      datasets: [{
        label: "Mouth Aspect Ratio (MAR)",
        data: marChartData,
        borderColor: "#f59e0b",
        backgroundColor: "rgba(245, 158, 11, 0.08)",
        borderWidth: 2,
        tension: 0.3,
        fill: true,
        pointRadius: 0
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      scales: {
        x: { display: false },
        y: {
          min: 0.0,
          max: 0.9,
          grid: { color: "#232d3d" },
          ticks: { color: "#64748b", font: { family: "JetBrains Mono", size: 10 } }
        }
      },
      plugins: {
        legend: { display: false }
      }
    }
  });
}

function updateTelemetryCharts(data) {
  if (!earChartInstance || !marChartInstance) return;

  const nowTime = new Date().toLocaleTimeString();
  telemetryLabels.push(nowTime);
  earChartData.push(data.avg_ear || 0.0);
  marChartData.push(data.mar || 0.0);

  if (telemetryLabels.length > 70) {
    telemetryLabels.shift();
    earChartData.shift();
    marChartData.shift();
  }

  // Update Telemetry Header stats
  document.getElementById("telemFps").textContent = (data.fps || 0.0).toFixed(1);
  document.getElementById("telemTotalAlerts").textContent = data.total_alerts || 0;
  const d = data.session_duration || 0;
  document.getElementById("telemSessionTime").textContent = `${Math.floor(d / 60)}m ${Math.round(d % 60)}s`;
  document.getElementById("telemFaceStatus").textContent = data.face_detected ? "Active" : "No Face";

  earChartInstance.update("none");
  marChartInstance.update("none");
}

function clearTelemetryChart() {
  telemetryLabels.length = 0;
  earChartData.length    = 0;
  marChartData.length    = 0;
  if (earChartInstance) earChartInstance.update();
  if (marChartInstance) marChartInstance.update();
}

// ══════════════════════════════════════════════════════════
//  7. INCIDENT LOGS TABLE (SCREEN 5)
// ══════════════════════════════════════════════════════════
async function fetchLogsTable() {
  const tbody = document.getElementById("logsTableBody");
  try {
    const res = await fetch("/api/logs");
    const logs = await res.json();

    if (!logs || logs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center" style="padding:24px; color:var(--text-muted);">No drowsiness incidents recorded yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = logs.slice().reverse().map(ev => `
      <tr>
        <td>${ev.timestamp || "—"}</td>
        <td><span class="risk-badge highrisk">${ev.event_type || "HIGH_RISK_DROWSY"}</span></td>
        <td><strong style="color:var(--red)">${ev.ml_prediction || "Drowsy"}</strong></td>
        <td>${ev.avg_ear || "—"}</td>
        <td>${ev.mar || "—"}</td>
        <td>${ev.eye_closed_seconds || "—"}s</td>
      </tr>
    `).join("");
  } catch (err) {
    console.error("Fetch logs error:", err);
  }
}

async function clearLogs() {
  if (!confirm("Are you sure you want to clear all recorded incident logs?")) return;
  try {
    await fetch("/api/clear_logs", { method: "POST" });
    fetchLogsTable();
  } catch (e) {
    console.error(e);
  }
}

// ══════════════════════════════════════════════════════════
//  8. INITIALIZATION ON DOM READY
// ══════════════════════════════════════════════════════════
window.addEventListener("DOMContentLoaded", () => {
  initNavigation();
  initTelemetryCharts();

  // Run fast telemetry poll every 250ms
  setInterval(pollTelemetryState, 250);

  // Stop camera stream cleanly when closing tab
  window.addEventListener("beforeunload", () => {
    navigator.sendBeacon("/stop_camera");
  });
});
