document.addEventListener('DOMContentLoaded', function() {
    const config = window.zzyCaptchaConfig;
    if (!config || !config.siteKey || !config.selector) {
        console.error("zzyCaptcha: Configuration object (window.zzyCaptchaConfig) is missing or incomplete.");
        return;
    }

    const widgetContainer = document.querySelector(config.selector);
    if (!widgetContainer) {
        console.error(`zzyCaptcha: Container with selector '${config.selector}' not found.`);
        return;
    }

    let isVerified = false;

    // --- Create Widget & Modal HTML ---
    function renderInitialWidget() {
        widgetContainer.innerHTML = `
            <div class="zzy-captcha-widget">
                <div class="zzy-captcha-checkbox-container">
                    <div id="zzy-checkbox" class="zzy-captcha-checkbox">
                        <div class="checkmark"></div>
                    </div>
                    <span class="zzy-captcha-label">I am human</span>
                </div>
                <div class="zzy-captcha-logo">
                    <img src="/static/zzyss.png" alt="zzyCaptcha">
                    <span>zzyCaptcha</span>
                </div>
            </div>
            <div id="zzy-modal-overlay" class="zzy-captcha-modal-overlay">
                <div id="zzy-modal" class="zzy-captcha-modal">
                    <div class="zzy-captcha-modal-header">
                        <span>Verify your identity</span>
                        <span id="zzy-modal-close" class="zzy-captcha-modal-close">&times;</span>
                    </div>
                    <div id="zzy-modal-body" class="zzy-captcha-modal-body">
                        <!-- Iframe will be injected here -->
                    </div>
                </div>
            </div>
        `;
    }

    renderInitialWidget();

    // --- Get DOM Elements ---
    const checkbox = document.getElementById('zzy-checkbox');
    const modalOverlay = document.getElementById('zzy-modal-overlay');
    const modalBody = document.getElementById('zzy-modal-body');
    const closeButton = document.getElementById('zzy-modal-close');
    const form = widgetContainer.closest('form');
    const challengeIdInput = form ? form.querySelector('#zzy_challenge_id') : null;
    const userAnswerInput = form ? form.querySelector('#zzy_user_answer') : null;

    if (!form || !challengeIdInput || !userAnswerInput) {
        console.error("zzyCaptcha: Widget must be placed inside a form with hidden inputs #zzy_challenge_id and #zzy_user_answer.");
        return;
    }

    // --- Event Handlers ---
    function openModal() {
        if (isVerified) return; // Don't reopen if already verified
        modalOverlay.style.display = 'flex';
        // Create iframe just-in-time
        modalBody.innerHTML = `<iframe src="/api/challenge/${config.siteKey}"></iframe>`;
    }

    function closeModal() {
        modalOverlay.style.display = 'none';
        modalBody.innerHTML = ''; // Destroy iframe
    }

    checkbox.addEventListener('click', openModal);
    closeButton.addEventListener('click', closeModal);
    modalOverlay.addEventListener('click', (event) => {
        if (event.target === modalOverlay) {
            closeModal();
        }
    });

    // --- Listen for message from Iframe ---
    window.addEventListener('message', (event) => {
        // Basic security: check origin in production!
        // if (event.origin !== window.location.origin) return;

        const data = event.data;
        if (data.type === 'zzyCaptcha-response' && data.userAnswer) {
            console.log("CAPTCHA solved. Populating form.");
            challengeIdInput.value = data.challengeId;
            userAnswerInput.value = data.userAnswer;
            isVerified = true;
            checkbox.classList.add('verified');
            closeModal();
        }
    });
});