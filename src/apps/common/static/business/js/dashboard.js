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
    if (data.detail) return Array.isArray(data.detail) ? data.detail.join(" ") : data.detail;
    if (data.non_field_errors) return data.non_field_errors.join(" ");

    return Object.values(data).flat().join(" ") || "Erro inesperado.";
}

async function requestAPI(url, options = {}) {
    const response = await fetch(url, {
        ...options,
        credentials: "same-origin",
        headers: {
            "X-CSRFToken": getCSRFToken(),
            ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
            ...(options.headers || {}),
        },
    });

    if (response.status === 204) return null;

    const data = await response.json().catch(() => null);

    if (!response.ok) {
        throw new Error(parseAPIError(data));
    }

    return data;
}

function getResults(data) {
    return Array.isArray(data) ? data : data?.results || [];
}

function formatDate(value) {
    if (!value) return "Não informado";

    return new Intl.DateTimeFormat("pt-BR", {
        dateStyle: "short",
        timeStyle: "short",
    }).format(new Date(value));
}

function getInitials(value) {
    return String(value || "CH")
        .trim()
        .split(/\s+/)
        .slice(0, 2)
        .map((part) => part[0])
        .join("")
        .toUpperCase();
}

function parseAllowedIPs(value) {
    return String(value || "")
        .split(",")
        .map((ip) => ip.trim())
        .filter(Boolean);
}

async function loadBusinesses() {
    const data = await requestAPI(BUSINESS_URL);
    renderBusinesses(getResults(data));
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
        item.className = "business-item";

        item.innerHTML = `
            <div class="item-media">
                ${
                    business.picture
                        ? `<img src="${business.picture}" alt="Logo de ${business.name}">`
                        : `<span>${getInitials(business.name)}</span>`
                }
            </div>

            <div class="item-content">
                <strong>${business.name}</strong>
                <p>${business.summary || "Sem resumo"}</p>

                <div class="item-meta">
                    <span>${business.restricted_network ? "Rede restrita" : "Rede livre"}</span>
                    <span>${business.restricted_gps ? "GPS restrito" : "GPS livre"}</span>
                </div>

                ${
                    business.short_link
                        ? `<a href="${business.short_link}" target="_blank" rel="noopener">Abrir link curto</a>`
                        : ""
                }
            </div>

            <div class="item-actions">
                <button type="button" onclick='selectBusiness(${JSON.stringify(business)})'>Abrir</button>
                <button type="button" onclick='editBusiness(${JSON.stringify(business)})'>Editar</button>
                <button type="button" class="danger" onclick="deleteBusiness('${business.public_uuid}')">Excluir</button>
            </div>
        `;

        list.appendChild(item);
    });
}

async function selectBusiness(business) {
    selectedBusiness = business;

    document.getElementById("employees-title").textContent = business.name;
    document.getElementById("employees-description").textContent = "Funcionários cadastrados nesta empresa.";
    document.getElementById("create-employee-button").classList.remove("hidden");

    await loadEmployees();
}

async function loadEmployees() {
    if (!selectedBusiness) return;

    const data = await requestAPI(`${BUSINESS_URL}${selectedBusiness.public_uuid}/employees/`);
    renderEmployees(getResults(data));
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
        item.className = "business-item";

        item.innerHTML = `
            <div class="item-media">
                ${
                    employee.picture
                        ? `<img src="${employee.picture}" alt="Foto de ${employee.name}">`
                        : `<span>${getInitials(employee.name)}</span>`
                }
            </div>

            <div class="item-content">
                <strong>${employee.name}</strong>
                <p>Matrícula ${employee.register || "não informada"}</p>

                <div class="item-meta">
                    <span>${employee.is_active ? "Ativo" : "Inativo"}</span>
                </div>
            </div>

            <div class="item-actions">
                <button type="button" onclick='editEmployee(${JSON.stringify(employee)})'>Editar</button>
                <button type="button" class="danger" onclick="deleteEmployee('${employee.public_uuid}')">Excluir</button>
            </div>
        `;

        list.appendChild(item);
    });
}

function openBusinessModal() {
    document.getElementById("business-form").reset();
    document.getElementById("business-uuid").value = "";
    document.getElementById("business-modal-title").textContent = "Nova empresa";
    document.getElementById("business-modal").showModal();
}

function closeBusinessModal() {
    document.getElementById("business-modal").close();
}

function editBusiness(business) {
    document.getElementById("business-modal-title").textContent = "Editar empresa";
    document.getElementById("business-uuid").value = business.public_uuid || "";

    document.getElementById("business-name").value = business.name || "";
    document.getElementById("business-summary").value = business.summary || "";
    document.getElementById("business-description").value = business.description || "";

    document.getElementById("business-restricted-network").checked = Boolean(business.restricted_network);
    document.getElementById("business-restricted-gps").checked = Boolean(business.restricted_gps);

    document.getElementById("business-allowed-ips").value = (business.allowed_ips || []).join(", ");
    document.getElementById("business-lat").value = business.lat ?? "";
    document.getElementById("business-lng").value = business.lng ?? "";
    document.getElementById("business-radius").value = business.allowed_radius_meters ?? 100;

    document.getElementById("business-modal").showModal();
}

async function saveBusiness(event) {
    event.preventDefault();

    const uuid = document.getElementById("business-uuid").value;
    const picture = document.getElementById("business-picture").files[0];

    const formData = new FormData();

    formData.append("name", document.getElementById("business-name").value.trim());
    formData.append("summary", document.getElementById("business-summary").value.trim());
    formData.append("description", document.getElementById("business-description").value.trim());

    formData.append("restricted_network", document.getElementById("business-restricted-network").checked);
    formData.append("restricted_gps", document.getElementById("business-restricted-gps").checked);

    const lat = document.getElementById("business-lat").value;
    const lng = document.getElementById("business-lng").value;
    const radius = document.getElementById("business-radius").value;

    if (lat) formData.append("lat", lat);
    if (lng) formData.append("lng", lng);
    if (radius) formData.append("allowed_radius_meters", radius);

    parseAllowedIPs(document.getElementById("business-allowed-ips").value).forEach((ip) => {
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

        closeBusinessModal();
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
            document.getElementById("employees-description").textContent = "Selecione uma empresa.";
            document.getElementById("create-employee-button").classList.add("hidden");

            const list = document.getElementById("employee-list");
            list.className = "list empty";
            list.textContent = "Nenhuma empresa selecionada.";
        }

        await loadBusinesses();
        showMessage("Empresa excluída com sucesso.");
    } catch (error) {
        showMessage(error.message, true);
    }
}

function openEmployeeModal() {
    if (!selectedBusiness) {
        showMessage("Selecione uma empresa primeiro.", true);
        return;
    }

    document.getElementById("employee-form").reset();
    document.getElementById("employee-uuid").value = "";
    document.getElementById("employee-is-active").checked = true;
    document.getElementById("employee-modal-title").textContent = "Novo funcionário";
    document.getElementById("employee-modal").showModal();
}

function closeEmployeeModal() {
    document.getElementById("employee-modal").close();
}

function editEmployee(employee) {
    document.getElementById("employee-modal-title").textContent = "Editar funcionário";
    document.getElementById("employee-uuid").value = employee.public_uuid || "";

    document.getElementById("employee-name").value = employee.name || "";
    document.getElementById("employee-register").value = employee.register || "";
    document.getElementById("employee-is-active").checked = Boolean(employee.is_active);

    document.getElementById("employee-modal").showModal();
}

async function saveEmployee(event) {
    event.preventDefault();

    if (!selectedBusiness) return;

    const uuid = document.getElementById("employee-uuid").value;
    const picture = document.getElementById("employee-picture").files[0];

    const formData = new FormData();

    formData.append("name", document.getElementById("employee-name").value.trim());
    formData.append("register", document.getElementById("employee-register").value.trim());
    formData.append("is_active", document.getElementById("employee-is-active").checked);

    if (picture) {
        formData.append("picture", picture);
    }

    const url = `${BUSINESS_URL}${selectedBusiness.public_uuid}/employees/`;

    try {
        await requestAPI(uuid ? `${url}${uuid}/` : url, {
            method: uuid ? "PATCH" : "POST",
            body: formData,
        });

        closeEmployeeModal();
        await loadEmployees();

        showMessage(uuid ? "Funcionário atualizado com sucesso." : "Funcionário criado com sucesso.");
    } catch (error) {
        showMessage(error.message, true);
    }
}

async function deleteEmployee(uuid) {
    if (!selectedBusiness) return;
    if (!confirm("Deseja excluir este funcionário?")) return;

    try {
        await requestAPI(`${BUSINESS_URL}${selectedBusiness.public_uuid}/employees/${uuid}/`, {
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