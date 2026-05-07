const businessUUID = window.CHRONOS_CONFIG.businessUUID;
const PROFILE_URL = window.CHRONOS_CONFIG.profileURL;
const CLOCKING_URL = window.CHRONOS_CONFIG.clockingURL;
const RECORD_TYPES = {
    entry: {
        label: "Entrada",
        timeline: "Entrada registrada",
        className: "entry",
    },
    break_start: {
        label: "Intervalo",
        timeline: "Intervalo iniciado",
        className: "break-start",
    },
    break_end: {
        label: "Volta",
        timeline: "Retorno registrado",
        className: "break-end",
    },
    exit: {
        label: "Saída",
        timeline: "Saída registrada",
        className: "exit",
    },
};

let employeeToken = localStorage.getItem("employeeToken");
let currentSession = null;
let isClocking = false;

function getCSRFToken() {
    return document.querySelector("[name=csrfmiddlewaretoken]")?.value || "";
}

function showMessage(message, isError = false) {
    const el = document.getElementById("message");
    el.textContent = message;
    el.className = "message " + (isError ? "error" : "success");
}

function generateEmployeeToken(register, pin) {
    return btoa(`${businessUUID},${register},${pin}`);
}

function parseAPIError(data) {
    if (!data) return "Erro inesperado";
    if (typeof data === "string") return data;
    if (data.detail) return Array.isArray(data.detail) ? data.detail.join(" ") : data.detail;
    if (data.non_field_errors) return data.non_field_errors.join(" ");
    return Object.values(data).flat().join(" ") || "Erro inesperado";
}

function getInitials(value) {
    const parts = String(value || "")
        .trim()
        .split(/\s+/)
        .filter(Boolean)
        .slice(0, 2);

    return parts.map((part) => part[0]).join("").toUpperCase() || "CH";
}

async function requestAPI(url, options = {}) {
    const { allowNotFound = false, ...fetchOptions } = options;
    const response = await fetch(url, {
        ...fetchOptions,
        credentials: "same-origin",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken(),
            "employee-token": employeeToken,
            ...(fetchOptions.headers || {}),
        },
    });

    const data = await response.json().catch(() => null);

    if (allowNotFound && response.status === 404) {
        return null;
    }

    if (!response.ok) {
        throw new Error(parseAPIError(data));
    }

    return data;
}

function getSessionRecords(session = currentSession) {
    return [...(session?.time_records || [])].sort((a, b) => {
        return new Date(a.registred_at) - new Date(b.registred_at);
    });
}

function getLastRecord(session = currentSession) {
    const records = getSessionRecords(session);
    return records.length ? records[records.length - 1] : null;
}

function formatRecordTime(value) {
    if (!value) return "--:--";

    return new Intl.DateTimeFormat("pt-BR", {
        hour: "2-digit",
        minute: "2-digit",
    }).format(new Date(value));
}

function formatDuration(startAt) {
    if (!startAt) return "00h00";

    const diffInMinutes = Math.max(
        0,
        Math.floor((new Date() - new Date(startAt)) / 60000)
    );
    const hours = Math.floor(diffInMinutes / 60);
    const minutes = diffInMinutes % 60;

    return `${String(hours).padStart(2, "0")}h${String(minutes).padStart(2, "0")}`;
}

function setSessionStatus(type, text) {
    const status = document.getElementById("session-status");
    document.getElementById("session-status-text").textContent = text;
    status.className = `status-pill ${type}`;
}

function renderSessionDuration() {
    document.getElementById("session-duration").textContent = formatDuration(
        currentSession?.start_at
    );
}

function getEnabledRecordTypes(session = currentSession) {
    const lastRecord = getLastRecord(session);

    if (!session) return ["entry"];
    if (lastRecord?.type === "break_start") return ["break_end"];
    if (lastRecord?.type === "entry" || lastRecord?.type === "break_end") {
        return ["break_start", "exit"];
    }

    return [];
}

function setActionAvailability() {
    const enabledRecordTypes = getEnabledRecordTypes();
    document.querySelectorAll("[data-record-type]").forEach((button) => {
        button.disabled =
            isClocking || !enabledRecordTypes.includes(button.dataset.recordType);
    });
}

function renderTimeline(records) {
    const timeline = document.getElementById("session-timeline");
    timeline.replaceChildren();

    if (!records.length) {
        const empty = document.createElement("li");
        empty.className = "timeline-empty";
        empty.textContent = "Nenhum registro na jornada atual.";
        timeline.appendChild(empty);
        return;
    }

    records.forEach((record) => {
        const recordType = RECORD_TYPES[record.type] || {
            timeline: record.type,
            className: "",
        };
        const item = document.createElement("li");
        item.className = `timeline-item ${recordType.className}`;

        const marker = document.createElement("span");
        marker.className = "timeline-marker";
        marker.setAttribute("aria-hidden", "true");

        const copy = document.createElement("span");
        const title = document.createElement("strong");
        title.className = "timeline-title";
        title.textContent = recordType.timeline;

        const ip = document.createElement("span");
        ip.className = "timeline-ip";
        ip.textContent = record.client_ip ? `IP ${record.client_ip}` : "IP não informado";

        const time = document.createElement("time");
        time.className = "timeline-time";
        time.dateTime = record.registred_at;
        time.textContent = formatRecordTime(record.registred_at);

        copy.append(title, ip);
        item.append(marker, copy, time);
        timeline.appendChild(item);
    });
}

function renderCurrentSession() {
    const card = document.getElementById("session-card");
    const records = getSessionRecords();
    const lastRecord = records.length ? records[records.length - 1] : null;
    const lastRecordType = RECORD_TYPES[lastRecord?.type];

    if (!currentSession) {
        card.classList.add("empty");
        document.getElementById("session-title").textContent = "Nenhuma jornada iniciada";
        document.getElementById("session-start").textContent = "--:--";
        document.getElementById("session-last").textContent = "Nenhum";
        renderSessionDuration();
        renderTimeline([]);
        setSessionStatus("idle", "Sem jornada");
        setActionAvailability();
        return;
    }

    card.classList.remove("empty");
    document.getElementById("session-title").textContent =
        lastRecord?.type === "break_start"
            ? "Intervalo em andamento"
            : "Jornada em andamento";
    document.getElementById("session-start").textContent = formatRecordTime(
        currentSession.start_at
    );
    document.getElementById("session-last").textContent = lastRecord
        ? `${lastRecordType?.label || lastRecord.type} às ${formatRecordTime(lastRecord.registred_at)}`
        : "Nenhum";

    renderSessionDuration();
    renderTimeline(records);
    setSessionStatus(
        lastRecord?.type === "break_start" ? "break" : "",
        lastRecord?.type === "break_start" ? "Em intervalo" : "Em jornada"
    );
    setActionAvailability();
}

async function loadCurrentSession() {
    currentSession = await requestAPI(CLOCKING_URL, {
        method: "GET",
        allowNotFound: true,
    });
    renderCurrentSession();
    return currentSession;
}

async function loginEmployee(event) {
    event.preventDefault();

    const register = document.getElementById("register").value.trim();
    const pin = document.getElementById("pin").value.trim();

    if (!register || !pin) {
        showMessage("Informe matrícula e PIN", true);
        return;
    }

    employeeToken = generateEmployeeToken(register, pin);
    localStorage.setItem("employeeToken", employeeToken);

    try {
        await loadProfile();
        showMessage("Login realizado com sucesso");
    } catch (e) {
        localStorage.removeItem("employeeToken");
        employeeToken = null;
        showMessage(e.message, true);
    }
}

async function loadProfile() {
    if (!employeeToken) return;

    const employee = await requestAPI(PROFILE_URL);
    const employeeName = employee.name || "Colaborador";
    const businessName = employee.business?.name || "Empresa";

    document.getElementById("login-section").classList.add("hidden");
    document.getElementById("profile-section").classList.remove("hidden");
    document.getElementById("identity-section").classList.remove("hidden");

    document.getElementById("employee-name").textContent = employeeName;
    document.getElementById("employee-register").textContent =
        employee.register ? `Matrícula ${employee.register}` : "Sem matrícula";
    document.getElementById("employee-initials").textContent = getInitials(employeeName);

    document.getElementById("business-name").textContent = businessName;
    document.getElementById("business-summary").textContent =
        employee.business?.summary || "Sem resumo";
    document.getElementById("business-initials").textContent = getInitials(businessName);

    setImage("employee-picture", employee.picture, "employee-initials");
    setImage("business-picture", employee.business?.picture, "business-initials");
    await loadCurrentSession();
}

function setImage(id, url, fallbackId) {
    const el = document.getElementById(id);
    const fallback = fallbackId ? document.getElementById(fallbackId) : null;

    function showFallback() {
        el.classList.add("hidden");
        fallback?.classList.remove("hidden");
    }

    if (!url) {
        showFallback();
        return;
    }

    el.onerror = showFallback;
    el.src = url;
    el.classList.remove("hidden");
    fallback?.classList.add("hidden");
}

function logoutEmployee() {
    employeeToken = null;
    localStorage.removeItem("employeeToken");
    document.getElementById("profile-section").classList.add("hidden");
    document.getElementById("identity-section").classList.add("hidden");
    document.getElementById("login-section").classList.remove("hidden");
    document.getElementById("pin").value = "";
    currentSession = null;
    renderCurrentSession();
    showMessage("Sessão encerrada");
}

function updateCurrentTime() {
    const now = new Date();
    const time = now.toLocaleTimeString("pt-BR", {
        hour: "2-digit",
        minute: "2-digit",
    });
    const date = now.toLocaleDateString("pt-BR", {
        weekday: "long",
        day: "2-digit",
        month: "long",
    });

    document.getElementById("hero-time").textContent = time;
    document.getElementById("current-time").textContent = time;
    document.getElementById("today-date").textContent = date;
    document.getElementById("current-date").textContent = date;
    renderSessionDuration();
}

async function clocking(type) {
    if (isClocking) return;

    isClocking = true;
    setActionAvailability();

    try {
        await requestAPI(CLOCKING_URL, {
            method: "POST",
            body: JSON.stringify({ record_type: type }),
        });
        await loadCurrentSession();

        showMessage(type === "exit" ? "Jornada finalizada!" : "Ponto registrado!");
    } catch (e) {
        showMessage(e.message, true);
    } finally {
        isClocking = false;
        setActionAvailability();
    }
}

loadProfile().catch(() => {
    localStorage.removeItem("employeeToken");
    employeeToken = null;
    currentSession = null;
    document.getElementById("identity-section").classList.add("hidden");
    renderCurrentSession();
});
updateCurrentTime();
setInterval(updateCurrentTime, 1000);
