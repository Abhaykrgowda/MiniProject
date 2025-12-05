// frontend/app.js
(function () {

    const $ = s => document.querySelector(s);

    const fileInput = $('#fileInput');
    const dropzone = $('#dropzone');
    const uploadBtn = $('#uploadBtn');
    const thumbs = $('#thumbs');

    const resultLabel = $('#resultLabel');
    const resultConf = $('#resultConf');
    const annotatedImg = $('#annotatedImg');
    const errorBox = $('#errorBox');  // <-- NEW for custom UI errors


    // -------------------------
    // DRAG & DROP
    // -------------------------
    dropzone.addEventListener("click", () => fileInput.click());

    dropzone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropzone.classList.add("active");
    });

    dropzone.addEventListener("dragleave", (e) => {
        e.preventDefault();
        dropzone.classList.remove("active");
    });

    dropzone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropzone.classList.remove("active");

        const file = e.dataTransfer.files[0];
        if (file) {
            fileInput.files = e.dataTransfer.files;
            previewFile(file);
        }
    });


    // -------------------------
    // IMAGE PREVIEW
    // -------------------------
    fileInput.addEventListener("change", () => {
        previewFile(fileInput.files[0]);
    });

    function previewFile(file) {
        thumbs.innerHTML = "";
        if (!file) return;

        const img = document.createElement("img");
        img.src = URL.createObjectURL(file);
        thumbs.appendChild(img);
    }


    // -------------------------
    // UPLOAD + ANALYZE
    // -------------------------
    uploadBtn.addEventListener("click", async () => {

        const file = fileInput.files[0];
        if (!file) return alert("No file selected");

        errorBox.style.display = "none";   // clear previous errors

        const form = new FormData();
        form.append("file", file); // MUST match backend param name

        try {
            const BACKEND_URL = window.BACKEND_URL || `http://${window.location.hostname}:8000`;

            console.log("Using BACKEND_URL:", BACKEND_URL);

            const res = await fetch(`${BACKEND_URL}/predict`, {
                method: "POST",
                body: form
            });

            if (!res.ok) {
                let txt;
                try { txt = await res.text(); } catch (e) { txt = res.statusText; }
                showError(`Server Error: ${res.status}<br>${txt}`);
                return;
            }

            const j = await res.json();

            // -----------------------------
            // ❌ CASE 1: Image is NOT an X-ray
            // -----------------------------
            if (j.status === "error" && j.prediction === "Invalid Image") {
                annotatedImg.style.display = "none";
                resultLabel.innerHTML = `<span style="color:#ff5c5c; font-weight:700;">❌ Invalid Image</span>`;
                resultConf.innerText = `Confidence: ${(j.confidence * 100).toFixed(1)}%`;
                showError(`This image is <b>not an X-ray</b>. Please upload a valid X-ray.`);
                return;
            }

            if (j.status === "error") {
                showError(j.message || "Unknown backend error");
                return;
            }

            // -----------------------------
            // ✅ CASE 2: Valid X-ray + Prediction
            // -----------------------------
            resultLabel.innerText = j.prediction;
            resultConf.innerText = (j.confidence * 100).toFixed(1) + "%";

            if (j.annotated_url) {
                annotatedImg.src = `${BACKEND_URL}${j.annotated_url}`;
                annotatedImg.style.display = "block";
            }

        } catch (err) {
            console.error("Upload exception:", err);
            showError("Network Error: Unable to reach backend.<br>Check if the backend is running.");
        }
    });


    // -------------------------
    // ERROR UI FUNCTION
    // -------------------------
    function showError(msg) {
        errorBox.style.display = "block";
        errorBox.innerHTML = `
            <div style="
                padding:12px;
                border-radius:10px;
                background:#ffebeb;
                border:1px solid #ff9c9c;
                color:#b30000;
                font-weight:600;
                animation: fadeIn 0.3s ease-in-out;">
                ${msg}
            </div>
        `;
    }

})();
