/**
 * CropFlow Farm & Plot Data Collection JavaScript
 * Handles dynamic agronomic defaults, remaining water demand calculation preview,
 * intelligent Plot ID auto-generation and real-time uniqueness validation.
 */

document.addEventListener("DOMContentLoaded", function () {
    triggerDemandPreview();

    // Auto-fill next available Plot ID whenever modal opens
    const plotModal = document.getElementById("newPlotModal");
    if (plotModal) {
        plotModal.addEventListener("show.bs.modal", function () {
            const plotIdInput = document.getElementById("inputPlotId");
            if (plotIdInput) {
                // If input is empty or collides with an existing ID, auto-generate next
                if (!plotIdInput.value || (window.existingPlotIds && window.existingPlotIds.includes(plotIdInput.value.trim()))) {
                    generateNextPlotId();
                }
            }
        });
    }
});

/**
 * Computes the next guaranteed unique Plot ID based on existing plots in the farm.
 * e.g., P-101 .. P-106 -> P-107; P-10001 -> P-10002.
 */
function computeNextPlotId() {
    const ids = window.existingPlotIds || [];
    let maxNum = 100;
    let hasMatch = false;

    for (const id of ids) {
        const match = id.match(/(\d+)/);
        if (match) {
            const num = parseInt(match[1], 10);
            if (!isNaN(num) && num > maxNum) {
                maxNum = num;
                hasMatch = true;
            }
        }
    }

    if (!hasMatch && ids.length === 0) {
        return "P-101";
    }

    return `P-${maxNum + 1}`;
}

/**
 * Generates and sets the next unique Plot ID into the input field.
 */
function generateNextPlotId() {
    const input = document.getElementById("inputPlotId");
    if (!input) return;
    const nextId = computeNextPlotId();
    input.value = nextId;
    input.classList.remove("is-invalid");
    const errEl = document.getElementById("err_plot_identifier");
    if (errEl) errEl.innerHTML = "";
    const hint = document.getElementById("plotIdHint");
    if (hint) {
        hint.innerHTML = `<span class="text-success"><i class="bi bi-check-circle-fill me-1"></i>Generated unique ID: <strong>${nextId}</strong></span>`;
    }
}

/**
 * Instantly applies a suggested Plot ID when the user clicks the suggestion link.
 */
function useSuggestedPlotId(id) {
    const input = document.getElementById("inputPlotId");
    if (input) {
        input.value = id;
        input.classList.remove("is-invalid");
    }
    const errEl = document.getElementById("err_plot_identifier");
    if (errEl) errEl.innerHTML = "";
    const hint = document.getElementById("plotIdHint");
    if (hint) {
        hint.innerHTML = `<span class="text-success"><i class="bi bi-check-circle-fill me-1"></i>Selected unique ID: <strong>${id}</strong></span>`;
    }
}

/**
 * Real-time validation as the user types a Plot ID.
 * Prevents submitting duplicate IDs and provides an immediate one-click fix.
 */
function checkPlotIdLive(val) {
    const cleanVal = (val || "").trim();
    const input = document.getElementById("inputPlotId");
    const errEl = document.getElementById("err_plot_identifier");
    const hint = document.getElementById("plotIdHint");

    if (!input || !errEl) return;

    if (!cleanVal) {
        input.classList.remove("is-invalid");
        errEl.innerHTML = "";
        if (hint) hint.textContent = "Must be unique within farm";
        return;
    }

    if (window.existingPlotIds && window.existingPlotIds.includes(cleanVal)) {
        input.classList.add("is-invalid");
        const nextId = computeNextPlotId();
        const msg = (typeof window.CropFlowI18n !== "undefined")
            ? window.CropFlowI18n.t("err_plot_id_exists")
            : "Plot ID already exists in this farm.";
        const suggestText = (typeof window.CropFlowI18n !== "undefined")
            ? window.CropFlowI18n.t("err_plot_id_suggest")
            : "already exists. Click here to use next available ID:";

        errEl.innerHTML = `
            ${msg} <span class="d-block mt-1">Suggested: <a href="javascript:void(0)" class="fw-bold text-decoration-underline text-primary" onclick="useSuggestedPlotId('${nextId}')">${nextId}</a></span>
        `;
        if (hint) hint.innerHTML = `<span class="text-danger fw-semibold"><i class="bi bi-exclamation-triangle-fill me-1"></i>Duplicate ID conflict</span>`;
    } else {
        input.classList.remove("is-invalid");
        errEl.innerHTML = "";
        if (hint) hint.innerHTML = `<span class="text-success"><i class="bi bi-check-circle-fill me-1"></i>Plot ID '${cleanVal}' is available</span>`;
    }
}

function triggerDemandPreview() {
    const area = parseFloat(document.getElementById("inputArea")?.value || "1.0");
    const reqLiters = parseFloat(document.getElementById("inputReqLiters")?.value || "100000.0");
    const currentM = parseFloat(document.getElementById("inputCurrentM")?.value || "30.0");
    const targetM = parseFloat(document.getElementById("inputTargetM")?.value || "75.0");
    const soilType = document.getElementById("inputSoil")?.value || "Loamy";

    const previewVal = document.getElementById("demandPreviewVal");
    const previewM3 = document.getElementById("demandPreviewM3");
    const assumptionsLog = document.getElementById("assumptionsLog");
    const statusBadge = document.getElementById("soilStatusBadge");

    if (!previewVal) return;

    // Soil specific wilting point
    const wiltingPoints = { "Sandy": 9.0, "Loamy": 14.0, "Clay": 18.0 };
    const wp = wiltingPoints[soilType] || 15.0;

    if (currentM >= targetM) {
        previewVal.textContent = "0 Liters";
        if (previewM3) previewM3.textContent = "(0.00 m³)";
        if (statusBadge) statusBadge.textContent = "Status: Saturated / Target Achieved";
        if (assumptionsLog) {
            assumptionsLog.innerHTML = `&bull; Current moisture (${currentM}%) &ge; Target moisture (${targetM}%). No irrigation required.`;
        }
        return;
    }

    const range = Math.max(1.0, targetM - wp);
    const deficit = Math.max(0.0, targetM - currentM);
    const ratio = Math.min(1.0, deficit / range);

    const remainingLiters = Math.round(reqLiters * ratio);
    const remainingM3 = (remainingLiters / 1000.0).toFixed(2);

    previewVal.textContent = `${remainingLiters.toLocaleString()} Liters`;
    if (previewM3) previewM3.textContent = `(${remainingM3} m³)`;
    if (statusBadge) statusBadge.textContent = `Status: Active Deficit (${(ratio * 100).toFixed(1)}% of need)`;

    if (assumptionsLog) {
        assumptionsLog.innerHTML = `
            &bull; Available water capacity: ${targetM}% - ${wp}% = ${range.toFixed(1)}%<br>
            &bull; Current deficit: ${deficit.toFixed(1)}% &rarr; Deficit ratio: ${(ratio * 100).toFixed(1)}%<br>
            &bull; Remaining demand: ${reqLiters.toLocaleString()} L &times; ${(ratio * 100).toFixed(1)}% = ${remainingLiters.toLocaleString()} Liters
        `;
    }
}

function updateSoilDefaults(soil) {
    const infInput = document.getElementById("inputInfRate");
    const targetInput = document.getElementById("inputTargetM");
    if (!infInput || !targetInput) return;

    if (soil === "Sandy") {
        infInput.value = "25.0";
        targetInput.value = "65.0";
    } else if (soil === "Clay") {
        infInput.value = "10.0";
        targetInput.value = "80.0";
    } else {
        infInput.value = "16.0";
        targetInput.value = "75.0";
    }
}

function updateStageSensitivity(stage) {
    // Informative update based on crop stage
}

function autoFillCropDefaults(crop) {
    // Crop defaults helper
}

function clearFormErrors(formId, alertId) {
    const form = document.getElementById(formId);
    if (form) {
        const inputs = form.querySelectorAll(".is-invalid");
        inputs.forEach(el => el.classList.remove("is-invalid"));
        const feedbacks = form.querySelectorAll(".invalid-feedback");
        feedbacks.forEach(el => el.innerHTML = "");
    }
    const alertBox = document.getElementById(alertId);
    if (alertBox) {
        alertBox.classList.add("d-none");
        alertBox.innerHTML = "";
    }
}

function displayFormErrors(formId, alertId, errors) {
    const alertBox = document.getElementById(alertId);
    if (alertBox) {
        const errorPrompt = (typeof window.CropFlowI18n !== "undefined")
            ? window.CropFlowI18n.t("err_correct_inputs")
            : "Please correct the highlighted inputs below.";
        alertBox.innerHTML = errorPrompt;
        alertBox.classList.remove("d-none");
    }

    for (const [field, msg] of Object.entries(errors)) {
        const input = document.querySelector(`#${formId} [name="${field}"]`);
        const errEl = document.getElementById(`err_${field}`);
        if (input) {
            input.classList.add("is-invalid");
        }
        if (errEl) {
            if (field === "plot_identifier" && msg.includes("already exists")) {
                const nextId = computeNextPlotId();
                errEl.innerHTML = `${msg} <span class="d-block mt-1">Suggested: <a href="javascript:void(0)" class="fw-bold text-decoration-underline text-primary" onclick="useSuggestedPlotId('${nextId}')">${nextId}</a></span>`;
            } else {
                errEl.innerHTML = msg;
            }
        }
    }
}

function submitNewFarm(e) {
    e.preventDefault();
    clearFormErrors("createFarmForm", "farmFormAlert");

    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Saving...';
    }

    const formData = new FormData(form);
    const payload = Object.fromEntries(formData.entries());

    fetch('/api/farms', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
    .then(async r => {
        const data = await r.json();
        if (!r.ok) {
            if (data.field_errors) {
                displayFormErrors("createFarmForm", "farmFormAlert", data.field_errors);
            } else {
                alert(data.error || "Failed to create farm.");
            }
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Save Farm';
            }
            return;
        }
        window.location.href = `/farms?farm_id=${data.farm_id}`;
    })
    .catch(err => {
        console.error("Error creating farm:", err);
        alert("Network error connecting to CropFlow server.");
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Save Farm';
        }
    });
}

function submitNewPlot(e) {
    e.preventDefault();
    clearFormErrors("createPlotForm", "plotFormAlert");

    if (!window.currentFarmId) {
        alert("Please select or create a farm first.");
        return;
    }

    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Saving...';
    }

    const formData = new FormData(form);
    const payload = Object.fromEntries(formData.entries());

    fetch(`/api/farms/${window.currentFarmId}/plots`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
    .then(async r => {
        const data = await r.json();
        if (!r.ok) {
            if (data.field_errors) {
                displayFormErrors("createPlotForm", "plotFormAlert", data.field_errors);
            } else {
                alert(data.error || "Failed to add plot.");
            }
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Save Plot';
            }
            return;
        }
        window.location.reload();
    })
    .catch(err => {
        console.error("Error adding plot:", err);
        alert("Network error adding plot.");
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Save Plot';
        }
    });
}

function deletePlot(plotId) {
    if (!confirm(`Are you sure you want to delete plot #${plotId}?`)) return;

    fetch(`/api/plots/${plotId}`, {
        method: 'DELETE'
    })
    .then(r => r.json())
    .then(() => {
        window.location.reload();
    })
    .catch(err => {
        console.error("Error deleting plot:", err);
        alert("Failed to delete plot.");
    });
}

function reseedSampleData() {
    if (!confirm("Reset database to sample farm with 6 testing plots?")) return;

    fetch('/api/farms/seed', {
        method: 'POST'
    })
    .then(r => r.json())
    .then(() => {
        window.location.href = '/farms';
    })
    .catch(err => {
        console.error("Error resetting data:", err);
        alert("Failed to reset sample data.");
    });
}
