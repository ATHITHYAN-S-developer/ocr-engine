const API_BASE = '/api/v1';

// Global App State
let token = localStorage.getItem('ocr_jwt') || null;
let activeProjectId = null;
let activeJobId = null;
let activeJobResult = null;
let pollingIntervals = {};
let activeCanvasPage = 1;

// Document Elements
const loginForm = document.getElementById('login-form');
const authSection = document.getElementById('auth-section');
const authUserInfo = document.getElementById('auth-user-info');
const loggedUserEmail = document.getElementById('logged-user-email');
const btnLogout = document.getElementById('btn-logout');
const projectSection = document.getElementById('project-section');
const projectSelector = document.getElementById('project-selector');
const btnCreateProject = document.getElementById('btn-create-project');
const btnGenKey = document.getElementById('btn-gen-key');
const apiKeysList = document.getElementById('api-keys-list');
const dragDropZone = document.getElementById('drag-drop-zone');
const fileInput = document.getElementById('file-input');
const uploadProgressList = document.getElementById('upload-progress-list');
const jobsList = document.getElementById('jobs-list');
const workspaceViewer = document.getElementById('workspace-viewer');
const documentCanvas = document.getElementById('document-canvas');
const pageIndicator = document.getElementById('page-num-indicator');
const btnPrevPage = document.getElementById('btn-prev-page');
const btnNextPage = document.getElementById('btn-next-page');

// Modal Elements
const projectModal = document.getElementById('project-modal');
const createProjectForm = document.getElementById('create-project-form');
const btnCancelProject = document.getElementById('btn-cancel-project');

// Tabs & Exporters
const tabButtons = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');
const btnExports = document.querySelectorAll('.btn-export');

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    checkHealth();
    setInterval(checkHealth, 30000); // Check health every 30 seconds

    if (token) {
        setLoggedInState(token);
    }

    setupEventListeners();
});

// Event Listeners setup
function setupEventListeners() {
    // Auth Form
    loginForm.addEventListener('submit', handleLogin);
    document.getElementById('btn-register').addEventListener('click', handleRegister);
    btnLogout.addEventListener('click', handleLogout);

    // Project creation triggers
    btnCreateProject.addEventListener('click', () => projectModal.classList.remove('hidden'));
    btnCancelProject.addEventListener('click', () => projectModal.classList.add('hidden'));
    createProjectForm.addEventListener('submit', handleCreateProject);
    projectSelector.addEventListener('change', (e) => {
        activeProjectId = e.target.value;
        if (activeProjectId) {
            loadAPIKeys();
        }
    });

    // API Key generation
    btnGenKey.addEventListener('click', handleGenerateAPIKey);

    // Upload triggers
    dragDropZone.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileSelect);
    dragDropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dragDropZone.classList.add('dragover');
    });
    dragDropZone.addEventListener('dragleave', () => {
        dragDropZone.classList.remove('dragover');
    });
    dragDropZone.addEventListener('drop', handleFileDrop);

    // Tabs setup
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            tabButtons.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById(btn.dataset.tab).classList.add('active');
        });
    });

    // Export downloads
    btnExports.forEach(btn => {
        btn.addEventListener('click', () => {
            const format = btn.dataset.format;
            if (activeJobId) {
                downloadExportFile(activeJobId, format);
            }
        });
    });

    // Canvas Page control
    btnPrevPage.addEventListener('click', () => {
        if (activeCanvasPage > 1) {
            activeCanvasPage--;
            renderPageLayout(activeCanvasPage);
        }
    });
    btnNextPage.addEventListener('click', () => {
        if (activeJobResult && activeCanvasPage < activeJobResult.structured_json.pages.length) {
            activeCanvasPage++;
            renderPageLayout(activeCanvasPage);
        }
    });
}

// Helpers for API requests
async function apiCall(endpoint, options = {}) {
    const headers = options.headers || {};
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    options.headers = headers;

    const response = await fetch(`${API_BASE}${endpoint}`, options);
    if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || `Request failed with code ${response.status}`);
    }
    return response.json();
}

// Health Checker
async function checkHealth() {
    try {
        const res = await fetch(`${API_BASE}/health`);
        const data = await res.json();
        
        const dbDot = document.getElementById('health-db');
        const redisDot = document.getElementById('health-redis');

        if (data.database === 'healthy') {
            dbDot.className = 'status-dot dot-green';
        } else {
            dbDot.className = 'status-dot dot-red';
        }

        if (data.redis === 'healthy') {
            redisDot.className = 'status-dot dot-green';
        } else {
            redisDot.className = 'status-dot dot-red';
        }
    } catch (e) {
        document.getElementById('health-db').className = 'status-dot dot-red';
        document.getElementById('health-redis').className = 'status-dot dot-red';
    }
}

// Auth Handlers
async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('auth-email').value;
    const password = document.getElementById('auth-password').value;

    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    try {
        const res = await fetch(`${API_BASE}/auth/token`, {
            method: 'POST',
            body: formData,
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });
        if (!res.ok) throw new Error("Authentication failed.");
        const data = await res.json();
        
        token = data.access_token;
        localStorage.setItem('ocr_jwt', token);
        setLoggedInState(token, email);
    } catch (err) {
        alert(err.message);
    }
}

async function handleRegister() {
    const email = document.getElementById('auth-email').value;
    const password = document.getElementById('auth-password').value;

    if (!email || !password) {
        alert("Please enter email and password to register.");
        return;
    }

    try {
        await apiCall('/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password, role: 'developer' })
        });
        alert("Account registered successfully! Please login.");
    } catch (err) {
        alert(err.message);
    }
}

function handleLogout() {
    token = null;
    localStorage.removeItem('ocr_jwt');
    loginForm.classList.remove('hidden');
    authUserInfo.classList.add('hidden');
    projectSection.classList.add('hidden');
    workspaceViewer.classList.add('hidden');
    // Clear list
    jobsList.innerHTML = `<tr><td colspan="5" class="text-center text-gray">No documents uploaded.</td></tr>`;
}

function setLoggedInState(jwtToken, email = null) {
    loginForm.classList.add('hidden');
    authUserInfo.classList.remove('hidden');
    projectSection.classList.remove('hidden');
    
    if (email) {
        loggedUserEmail.textContent = email;
    } else {
        // Fetch user info from token (decode claims)
        try {
            const payload = JSON.parse(atob(jwtToken.split('.')[1]));
            // Wait, we didn't store email in token, just sub (user ID)
            loggedUserEmail.textContent = "Developer Account";
        } catch (e) {
            loggedUserEmail.textContent = "Developer";
        }
    }
    loadProjects();
}

// Project Console Handlers
async function loadProjects() {
    try {
        const projects = await apiCall('/projects');
        projectSelector.innerHTML = '<option value="">-- Select Project --</option>';
        projects.forEach(p => {
            const opt = document.createElement('option');
            opt.value = p.id;
            opt.textContent = p.name;
            projectSelector.appendChild(opt);
        });
        if (projects.length > 0) {
            projectSelector.value = projects[0].id;
            activeProjectId = projects[0].id;
            loadAPIKeys();
        }
    } catch (err) {
        console.error(err);
    }
}

async function handleCreateProject(e) {
    e.preventDefault();
    const name = document.getElementById('new-proj-name').value;
    const description = document.getElementById('new-proj-desc').value;

    try {
        const proj = await apiCall('/projects', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, description })
        });
        projectModal.classList.add('hidden');
        createProjectForm.reset();
        await loadProjects();
        projectSelector.value = proj.id;
        activeProjectId = proj.id;
        loadAPIKeys();
    } catch (err) {
        alert(err.message);
    }
}

async function loadAPIKeys() {
    if (!activeProjectId) return;
    try {
        const keys = await apiCall(`/projects/${activeProjectId}/api-keys`);
        apiKeysList.innerHTML = '';
        keys.forEach(k => {
            const item = document.createElement('div');
            item.className = 'key-item';
            item.innerHTML = `
                <span>${k.name}</span>
                <span class="text-gray">${k.is_active ? 'Active' : 'Inactive'}</span>
            `;
            apiKeysList.appendChild(item);
        });
    } catch (err) {
        console.error(err);
    }
}

async function handleGenerateAPIKey() {
    if (!activeProjectId) {
        alert("Please select a project first.");
        return;
    }
    const name = prompt("Enter a friendly name for the API Key:");
    if (!name) return;

    try {
        const keyData = await apiCall(`/projects/${activeProjectId}/api-keys`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        });
        alert(`API Key Generated!\n\nName: ${keyData.name}\nKey: ${keyData.key}\n\nIMPORTANT: Copy this key now as you will not be able to see it again.`);
        loadAPIKeys();
    } catch (err) {
        alert(err.message);
    }
}

// Upload & Pipeline Execution Handlers
function handleFileDrop(e) {
    e.preventDefault();
    dragDropZone.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        uploadFiles(files);
    }
}

function handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
        uploadFiles(files);
    }
}

async function uploadFiles(files) {
    if (!activeProjectId) {
        alert("Please select or create a project before uploading.");
        return;
    }

    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        
        // Add progress item UI
        const item_id = 'up_' + Math.random().toString(36).substring(2, 9);
        const upItem = document.createElement('div');
        upItem.className = 'progress-item';
        upItem.id = item_id;
        upItem.innerHTML = `
            <span>${file.name}</span>
            <div class="progress-bar-bg"><div class="progress-bar-fg" id="bar-${item_id}"></div></div>
            <span id="percent-${item_id}">0%</span>
        `;
        uploadProgressList.appendChild(upItem);

        // Perform Upload
        const formData = new FormData();
        formData.append('file', file);

        try {
            const xhr = new XMLHttpRequest();
            xhr.open('POST', `${API_BASE}/documents`, true);
            if (token) {
                xhr.setRequestHeader('Authorization', `Bearer ${token}`);
            }
            xhr.setRequestHeader('x-api-key', ''); // Ensure headers clear for token path

            xhr.upload.onprogress = (evt) => {
                if (evt.lengthComputable) {
                    const percent = Math.round((evt.loaded / evt.total) * 100);
                    document.getElementById(`bar-${item_id}`).style.width = percent + '%';
                    document.getElementById(`percent-${item_id}`).textContent = percent + '%';
                }
            };

            xhr.onload = async () => {
                if (xhr.status === 201) {
                    const doc = JSON.parse(xhr.responseText);
                    upItem.remove(); // Clear progress bar
                    await submitOCRJob(doc.id, file.name);
                } else {
                    document.getElementById(`percent-${item_id}`).textContent = 'Error';
                    document.getElementById(`percent-${item_id}`).style.color = 'var(--danger)';
                }
            };

            xhr.onerror = () => {
                document.getElementById(`percent-${item_id}`).textContent = 'Failed';
            };

            xhr.send(formData);
        } catch (err) {
            console.error(err);
        }
    }
}

async function submitOCRJob(docId, filename) {
    try {
        const job = await apiCall('/jobs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                document_id: docId,
                engine_config: { recognition_engine: 'mock' }
            })
        });

        // Insert job into tracking table
        addJobToTable(job.id, filename, job.current_stage, job.progress, job.status);
        // Start live Celery progress polling
        startPollingJob(job.id);
    } catch (err) {
        alert(`Failed to start OCR Job: ${err.message}`);
    }
}

function addJobToTable(jobId, filename, stage, progress, status) {
    // Clear mock row if it exists
    if (jobsList.querySelector('.text-center')) {
        jobsList.innerHTML = '';
    }

    const row = document.createElement('tr');
    row.id = `job-row-${jobId}`;
    
    const progressPercent = Math.round(progress * 100);
    
    row.innerHTML = `
        <td><strong>${filename}</strong></td>
        <td id="job-stage-${jobId}">${stage}</td>
        <td>
            <div style="display:flex; align-items:center; gap:8px;">
                <div class="progress-bar-bg" style="margin:0; width:100px;"><div class="progress-bar-fg" id="job-bar-${jobId}" style="width: ${progressPercent}%"></div></div>
                <span id="job-percent-${jobId}">${progressPercent}%</span>
            </div>
        </td>
        <td><span class="status-badge status-badge-${status.toLowerCase()}" id="job-badge-${jobId}">${status}</span></td>
        <td>
            <button class="btn btn-secondary btn-sm btn-inspect hidden" id="job-btn-${jobId}" onclick="inspectJobResult('${jobId}')">Inspect</button>
        </td>
    `;
    
    // Add to table top
    jobsList.insertBefore(row, jobsList.firstChild);
}

function startPollingJob(jobId) {
    pollingIntervals[jobId] = setInterval(async () => {
        try {
            const job = await apiCall(`/jobs/${jobId}`);
            
            // Update row fields
            const progressPercent = Math.round(job.progress * 100);
            document.getElementById(`job-stage-${jobId}`).textContent = job.current_stage;
            document.getElementById(`job-bar-${jobId}`).style.width = progressPercent + '%';
            document.getElementById(`job-percent-${jobId}`).textContent = progressPercent + '%';
            
            const badge = document.getElementById(`job-badge-${jobId}`);
            badge.className = `status-badge status-badge-${job.status.toLowerCase()}`;
            badge.textContent = job.status;

            if (job.status === 'completed') {
                clearInterval(pollingIntervals[jobId]);
                // Show inspect button
                document.getElementById(`job-btn-${jobId}`).classList.remove('hidden');
                inspectJobResult(jobId);
            } else if (job.status === 'failed') {
                clearInterval(pollingIntervals[jobId]);
                alert(`OCR Job ${jobId} failed. Error: ${job.error_message}`);
            }
        } catch (e) {
            console.error("Polling error:", e);
        }
    }, 2000);
}

// Result Inspector and Visualizer
async function inspectJobResult(jobId) {
    activeJobId = jobId;
    try {
        const result = await apiCall(`/results/${jobId}`);
        activeJobResult = result;
        
        // Show Workspace Viewer split row
        workspaceViewer.classList.remove('hidden');
        workspaceViewer.scrollIntoView({ behavior: 'smooth' });

        // Update tabs content
        // 1. Raw Text
        document.getElementById('result-raw-text').textContent = result.raw_text;
        
        // 2. Structured JSON
        document.getElementById('result-json').textContent = JSON.stringify(result.structured_json, null, 2);

        // 3. Tables rendering
        const tablesDiv = document.getElementById('result-tables');
        tablesDiv.innerHTML = '';
        if (result.structured_json.tables && result.structured_json.tables.length > 0) {
            result.structured_json.tables.forEach((table, index) => {
                const title = document.createElement('h4');
                title.textContent = `Table ${index + 1} (Confidence: ${result.confidence})`;
                tablesDiv.appendChild(title);

                const htmlTable = document.createElement('table');
                htmlTable.className = 'data-table';
                
                // Heuristic row parsing
                const cells = table.cells;
                if (cells && cells.length > 0) {
                    const sorted_cells = [...cells].sort((a, b) => a.bbox.y_min - b.bbox.y_min || a.bbox.x_min - b.bbox.x_min);
                    const rows = [];
                    let current_row = [];
                    let last_y = -999.0;
                    
                    sorted_cells.forEach(c => {
                        if (last_y === -999.0 || Math.abs(c.bbox.y_min - last_y) < 15.0) {
                            current_row.push(c.text);
                            if (last_y === -999.0) last_y = c.bbox.y_min;
                        } else {
                            rows.push(current_row);
                            current_row = [c.text];
                            last_y = c.bbox.y_min;
                        }
                    });
                    if (current_row.length > 0) rows.push(current_row);

                    rows.forEach(r => {
                        const tr = document.createElement('tr');
                        r.forEach(cell_text => {
                            const td = document.createElement('td');
                            td.textContent = cell_text;
                            tr.appendChild(td);
                        });
                        htmlTable.appendChild(tr);
                    });
                }
                tablesDiv.appendChild(htmlTable);
            });
        } else {
            tablesDiv.innerHTML = '<p class="text-gray">No tables detected.</p>';
        }

        // 4. Entities rendering
        const entitiesDiv = document.getElementById('result-entities');
        entitiesDiv.innerHTML = '';
        if (result.structured_json.entities && result.structured_json.entities.length > 0) {
            result.structured_json.entities.forEach(ent => {
                const pill = document.createElement('span');
                pill.style.display = 'inline-block';
                pill.style.padding = '6px 12px';
                pill.style.margin = '4px';
                pill.style.borderRadius = '20px';
                pill.style.fontSize = '12px';
                pill.style.fontWeight = '500';
                
                let colorBg = 'rgba(139, 92, 246, 0.15)';
                let colorText = 'var(--primary)';
                if (ent.type === 'EMAIL') { colorBg = 'rgba(16, 185, 129, 0.15)'; colorText = 'var(--accent)'; }
                else if (ent.type === 'AMOUNT') { colorBg = 'rgba(245, 158, 11, 0.15)'; colorText = '#f59e0b'; }
                
                pill.style.backgroundColor = colorBg;
                pill.style.color = colorText;
                pill.innerHTML = `<strong>${ent.type}:</strong> ${ent.value}`;
                entitiesDiv.appendChild(pill);
            });
        } else {
            entitiesDiv.innerHTML = '<p class="text-gray">No entities extracted.</p>';
        }

        // 5. Draw Canvas boxes
        activeCanvasPage = 1;
        renderPageLayout(1);
    } catch (e) {
        alert(`Inspection failed: ${e.message}`);
    }
}

// Canvas Bounding Box Renderer
function renderPageLayout(pageNum) {
    if (!activeJobResult) return;
    const pages = activeJobResult.structured_json.pages;
    if (pageNum < 1 || pageNum > pages.length) return;

    const page = pages[pageNum - 1];
    
    // Page indicator update
    pageIndicator.textContent = `Page ${pageNum} of ${pages.length}`;
    btnPrevPage.disabled = (pageNum === 1);
    btnNextPage.disabled = (pageNum === pages.length);

    // Prepare Canvas size dynamically
    const canvas_w = page.width || 800;
    const canvas_h = page.height || 1100;
    
    // Resize viewport display width to fit screen
    const ratio = Math.min(600 / canvas_w, 1.0);
    documentCanvas.width = canvas_w * ratio;
    documentCanvas.height = canvas_h * ratio;

    const ctx = documentCanvas.getContext('2d');
    ctx.clearRect(0, 0, documentCanvas.width, documentCanvas.height);
    
    // 1. Draw Mock Page Background
    ctx.fillStyle = '#FFFFFF';
    ctx.fillRect(0, 0, documentCanvas.width, documentCanvas.height);
    
    // 2. Draw subtle layout rows/guide lines to look high-tech
    ctx.strokeStyle = '#f4f4f5';
    ctx.lineWidth = 0.5;
    for (let i = 20; i < documentCanvas.height; i += 20) {
        ctx.beginPath();
        ctx.moveTo(0, i);
        ctx.lineTo(documentCanvas.width, i);
        ctx.stroke();
    }

    // 3. Draw bounding boxes (from paragraphs and blocks)
    const blocks = page.blocks || [];
    blocks.forEach(block => {
        const box = block.bbox;
        const x = box.x_min * ratio;
        const y = box.y_min * ratio;
        const w = (box.x_max - box.x_min) * ratio;
        const h = (box.y_max - box.y_min) * ratio;

        // Draw Box Boundary
        ctx.strokeStyle = block.type === 'table' ? '#10b981' : '#8b5cf6';
        ctx.lineWidth = 1;
        ctx.strokeRect(x, y, w, h);

        // Draw light background inside box
        ctx.fillStyle = block.type === 'table' ? 'rgba(16, 185, 129, 0.05)' : 'rgba(139, 92, 246, 0.03)';
        ctx.fillRect(x, y, w, h);

        // Write short recognized text snippet inside bounding box
        ctx.fillStyle = '#27272a'; // dark zinc text
        ctx.font = '10px sans-serif';
        const txtSnippet = block.text.length > 30 ? block.text.substring(0, 27) + '...' : block.text;
        ctx.fillText(txtSnippet, x + 4, y + 14);
    });

    // Draw table cell grids
    const tables = page.tables || [];
    tables.forEach(table => {
        const cells = table.cells || [];
        cells.forEach(cell => {
            const bbox = cell.bbox;
            ctx.strokeStyle = 'rgba(16, 185, 129, 0.4)';
            ctx.lineWidth = 0.5;
            ctx.strokeRect(
                bbox.x_min * ratio, 
                bbox.y_min * ratio, 
                (bbox.x_max - bbox.x_min) * ratio, 
                (bbox.y_max - bbox.y_min) * ratio
            );
        });
    });
}

// Download Exporters Helper
async function downloadExportFile(jobId, format) {
    try {
        const headers = {};
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        const response = await fetch(`${API_BASE}/results/download/${jobId}/export?format=${format}`, {
            headers: headers
        });
        if (!response.ok) throw new Error("Could not download file.");
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `ocr_job_${jobId}.${format.toLowerCase()}`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
    } catch (err) {
        alert(`Download failed: ${err.message}`);
    }
}
