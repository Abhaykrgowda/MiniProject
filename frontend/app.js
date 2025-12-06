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
    const errorBox = $('#errorBox');


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

        errorBox.style.display = "none"; // clear old errors
        annotatedImg.style.display = "none"; // hide image preview
        resultConf.innerText = "";          // reset confidence

        const form = new FormData();
        form.append("file", file);

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
            // ❌ CASE 1 — NOT AN X-RAY IMAGE
            // -----------------------------
            if (j.status === "not_xray") {
                resultLabel.innerHTML = "❌ Not an X-ray Image";

                // Completely hide confidence
                resultConf.innerText = "";

                annotatedImg.style.display = "none";

                showError(
                    "The uploaded image is <b>not an X-ray</b>.<br>Please upload a radiographic X-ray image."
                );
                return;
            }


            // -----------------------------
            // ✅ CASE 2 — VALID X-RAY IMAGE
            // -----------------------------
            resultLabel.innerText = j.prediction;
            resultConf.innerText = (j.confidence * 100).toFixed(1) + "%";

            if (j.annotated_url) {
                annotatedImg.src = `${BACKEND_URL}${j.annotated_url}`;
                annotatedImg.style.display = "block";
            }

        } catch (err) {
            console.error("Upload exception:", err);
            showError("Network Error: Backend not reachable.<br>Check if the server is running.");
        }
    });


    // -------------------------
    // ERROR UI FUNCTION
    // -------------------------
    function showError(msg) {
        errorBox.style.display = "block";
        errorBox.innerHTML = `
            <div style="
                padding:14px;
                border-radius:12px;
                background:#ff4d4d;
                color:white;
                box-shadow:0 4px 12px rgba(0,0,0,0.25);
                font-size:15px;
                animation: fadeIn 0.25s ease-in-out;">
                ${msg}
            </div>
        `;
    }

})();
