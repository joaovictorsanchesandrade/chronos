const BUSINESS_URL = window.CHRONOS_CONFIG.businessURL;

let selectedBusiness = null;

function getCSRFToken() {
    return document.querySelector("[name=csrfmiddlewaretoken]")?.value || "";
}

function showMessage(message, isError = false) {
    const el = document.getElementById("message");

    el.textContent = message;
    el.className = `message ${isError ? "error" : "success"}`;
}

function parseAPIError(data) {
    if (!data) return "Erro inesperado.";
    if (typeof data === "string") return data;
    if (data.detail) return data.detail;
    if (data.non_field_errors) return data.non_field_errors.join(" ");

    return Object.values(data).flat().join(" ") || "Erro inesperado.";
}

async function requestAPI(url, options = {}) {
    const response = await fetch(url, {
        credentials: "same-origin",
        ...options,
        headers: {
            "X-CSRFToken": getCSRFToken(),
            ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
            ...(options.headers || {}),
        },
    });

    const data = await response.json().catch(() => null);

    if (!response.ok) {
        throw new Error(parseAPIError(data));
    }

    return data;
}

function getResults(data) {
    return Array.isArray(data) ? data : data.results || [];
}

async function loadBusinesses() {
    const data = await requestAPI(BUSINESS_URL);
    const businesses = getResults(data);

    renderBusinesses(businesses);
}

function renderBusinesses(businesses) {
    const list = document.getElementById("business-list");
    list.replaceChildren();

    if (!businesses.length) {
        list.className = "list empty";
        list.textContent = "Nenhuma empresa cadastrada.";
        return;
    }

    list.className = "list";

    businesses.forEach((business) => {
        const item = document.createElement("article");
        item.className = "list-item";

        item.innerHTML = `
            <div>
                <strong>${business.name}</strong>
                <p>${business.summary || "Sem resumo"}</p>
            </div>

            <div class="actions">
                <button type="button" onclick='selectBusiness(${JSON.stringify(business)})'>
                    Abrir
                </button>

                <button type="button" onclick='editBusiness(${JSON.stringify(business)})'>
                    Editar
                </button>

                <button type="button" class="danger" onclick="deleteBusiness('${business.public_uuid}')">
                    Excluir
                </button>
            </div>
        `;

        list.appendChild(item);
    });
}

async function selectBusiness(business) {
    selectedBusiness = business;

    document.getElementById("employees-title").textContent = business.name;
    document.getElementById("employees-subtitle").textContent = "Funcionários cadastrados nesta empresa.";
    document.getElementById("new-employee-button").classList.remove("hidden");

    await loadEmployees();
}

async function loadEmployees() {
    if (!selectedBusiness) return;

    const url = `${BUSINESS_URL}${selectedBusiness.public_uuid}/employees/`;
    const data = await requestAPI(url);
    const employees = getResults(data);

    renderEmployees(employees);
}

function renderEmployees(employees) {
    const list = document.getElementById("employee-list");
    list.replaceChildren();

    if (!employees.length) {
        list.className = "list empty";
        list.textContent = "Nenhum funcionário cadastrado.";
        return;
    }

    list.className = "list";

    employees.forEach((employee) => {
        const item = document.createElement("article");
        item.className = "list-item";

        item.innerHTML = `
            <div>
                <strong>${employee.name}</strong>
                <p>Matrícula ${employee.register || "-"}</p>
            </div>

            <div class="actions">
                <button type="button" onclick='editEmployee(${JSON.stringify(employee)})'>
                    Editar
                </button>

                <button type="button" class="danger" onclick="deleteEmployee('${employee.public_uuid}')">
                    Excluir
                </button>
            </div>
        `;

        list.appendChild(item);
    });
}

function openBusinessForm() {
    document.getElementById("business-form").reset();
    document.getElementById("business-uuid").value = "";
    document.getElementById("business-form-title").textContent = "Nova empresa";
    document.getElementById("business-dialog").showModal();
}

function closeBusinessForm() {
    document.getElementById("business-dialog").close();
}

function editBusiness(business) {
    document.getElementById("business-form-title").textContent = "Editar empresa";
    document.getElementById("business-uuid").value = business.public_uuid;

    document.getElementById("business-name").value = business.name || "";
    document.getElementById("business-summary").value = business.summary || "";
    document.getElementById("restricted-network").checked = Boolean(business.restricted_network);
    document.getElementById("restricted-gps").checked = Boolean(business.restricted_gps);
    document.getElementById("business-lat").value = business.lat || "";
    document.getElementById("business-lng").value = business.lng || "";
    document.getElementById("allowed-radius").value = business.allowed_radius_meters || 100;
    document.getElementById("allowed-ips").value = (business.allowed_ips || []).join(", ");

    document.getElementById("business-dialog").showModal();
}

async function submitBusiness(event) {
    event.preventDefault();

    const uuid = document.getElementById("business-uuid").value;
    const picture = document.getElementById("business-picture").files[0];

    const formData = new FormData();

    formData.append("name", document.getElementById("business-name").value);
    formData.append("summary", document.getElementById("business-summary").value);

    formData.append("restricted_network", document.getElementById("restricted-network").checked);
    formData.append("restricted_gps", document.getElementById("restricted-gps").checked);
    formData.append("lat", document.getElementById("business-lat").value);
    formData.append("lng", document.getElementById("business-lng").value);
    formData.append("allowed_radius_meters", document.getElementById("allowed-radius").value);

    const allowedIPs = document
        .getElementById("allowed-ips")
        .value
        .split(",")
        .map((ip) => ip.trim())
        .filter(Boolean);

    allowedIPs.forEach((ip) => {
        formData.append("allowed_ips", ip);
    });

    if (picture) {
        formData.append("picture", picture);
    }

    try {
        await requestAPI(uuid ? `${BUSINESS_URL}${uuid}/` : BUSINESS_URL, {
            method: uuid ? "PATCH" : "POST",
            body: formData,
        });

        closeBusinessForm();
        await loadBusinesses();

        showMessage(uuid ? "Empresa atualizada com sucesso." : "Empresa criada com sucesso.");
    } catch (error) {
        showMessage(error.message, true);
    }
}

async function deleteBusiness(uuid) {
    if (!confirm("Deseja excluir esta empresa?")) return;

    try {
        await requestAPI(`${BUSINESS_URL}${uuid}/`, {
            method: "DELETE",
        });

        if (selectedBusiness?.public_uuid === uuid) {
            selectedBusiness = null;
            document.getElementById("employees-title").textContent = "Funcionários";
            document.getElementById("employees-subtitle").textContent = "Selecione uma empresa para visualizar.";
            document.getElementById("new-employee-button").classList.add("hidden");
            document.getElementById("employee-list").className = "list empty";
            document.getElementById("employee-list").textContent = "Nenhuma empresa selecionada.";
        }

        await loadBusinesses();
        showMessage("Empresa excluída com sucesso.");
    } catch (error) {
        showMessage(error.message, true);
    }
}

function openEmployeeForm() {
    if (!selectedBusiness) {
        showMessage("Selecione uma empresa primeiro.", true);
        return;
    }

    document.getElementById("employee-form").reset();
    document.getElementById("employee-uuid").value = "";
    document.getElementById("employee-is-active").checked = true;
    document.getElementById("employee-form-title").textContent = "Novo funcionário";
    document.getElementById("employee-dialog").showModal();
}

function closeEmployeeForm() {
    document.getElementById("employee-dialog").close();
}

function editEmployee(employee) {
    document.getElementById("employee-form-title").textContent = "Editar funcionário";
    document.getElementById("employee-uuid").value = employee.public_uuid;

    document.getElementById("employee-name").value = employee.name || "";
    document.getElementById("employee-register").value = employee.register || "";
    document.getElementById("employee-is-active").checked = Boolean(employee.is_active);

    document.getElementById("employee-dialog").showModal();
}

async function submitEmployee(event) {
    event.preventDefault();

    if (!selectedBusiness) return;

    const uuid = document.getElementById("employee-uuid").value;
    const picture = document.getElementById("employee-picture").files[0];

    const formData = new FormData();

    formData.append("name", document.getElementById("employee-name").value);
    formData.append("register", document.getElementById("employee-register").value);
    formData.append("is_active", document.getElementById("employee-is-active").checked);

    if (picture) {
        formData.append("picture", picture);
    }

    const baseURL = `${BUSINESS_URL}${selectedBusiness.public_uuid}/employees/`;

    try {
        await requestAPI(uuid ? `${baseURL}${uuid}/` : baseURL, {
            method: uuid ? "PATCH" : "POST",
            body: formData,
        });

        closeEmployeeForm();
        await loadEmployees();

        showMessage(uuid ? "Funcionário atualizado com sucesso." : "Funcionário criado com sucesso.");
    } catch (error) {
        showMessage(error.message, true);
    }
}

async function deleteEmployee(uuid) {
    if (!selectedBusiness) return;
    if (!confirm("Deseja excluir este funcionário?")) return;

    const url = `${BUSINESS_URL}${selectedBusiness.public_uuid}/employees/${uuid}/`;

    try {
        await requestAPI(url, {
            method: "DELETE",
        });

        await loadEmployees();
        showMessage("Funcionário excluído com sucesso.");
    } catch (error) {
        showMessage(error.message, true);
    }
}

loadBusinesses().catch((error) => {
    showMessage(error.message, true);
});