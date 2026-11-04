const chatBox = document.getElementById('chat-box');
const scenes = {
    chat: document.getElementById('chat-container'),
    corp: document.getElementById('corp-container'),
    action: document.getElementById('action-container'),
    countdown: document.getElementById('countdown-container')
};

const TIMER_STORAGE_KEY = 'titan_flag11_deadline';

const script = [
    { sender: "slurr", text: "kopiko, ти тут?", delay: 1000 },
    { sender: "kopiko", text: "Так. Що трапилось?", delay: 3000 },
    { sender: "slurr", text: "Я щойно знайшов критичну діру в API Binance (v3).", delay: 2500 },
    { sender: "kopiko", text: "Ти серйозно? Це ж корпорація з мільярдними оборотами. Нас вичислять за хвилину.", delay: 4000 },
    { sender: "slurr", text: "Не вичислять, якщо зробимо все швидко. Їхній дебаг-роут забули закрити у проді.", delay: 4500 },
    { sender: "slurr", text: "Там лежать ключі доступу до Холодного Гаманця (Cold Wallet).", delay: 3000 },
    { sender: "kopiko", text: "Гаддем чувак. Це джекпот. Який план?", delay: 3500 },
    { sender: "slurr", text: "У нас є рівно 1 година, поки їхні адміни не зроблять ротацію токенів сесій.", delay: 4000 },
    { sender: "slurr", text: "Я піднімаю тунель на їхній Gateway. Забираємо прапор і зникаємо.", delay: 3500 }
];

function typeMessage(msgInfo) {
    return new Promise(resolve => {
        setTimeout(() => {
            const msgEl = document.createElement('div');
            msgEl.className = `msg ${msgInfo.sender}`;
            msgEl.innerHTML = `<div class="sender">[${msgInfo.sender}]</div><div class="text">${msgInfo.text}</div>`;
            chatBox.appendChild(msgEl);
            window.scrollTo(0, document.body.scrollHeight);
            resolve();
        }, msgInfo.delay);
    });
}

async function runIntro() {
    // 1. Chat Sequence
    for (let msg of script) {
        await typeMessage(msg);
    }
    
    // Wait before switching to corp
    await new Promise(r => setTimeout(r, 2000));
    scenes.chat.classList.remove('active');
    scenes.corp.classList.add('active');

    // 2. Corp Sequence (Wait 4s, then glitch)
    await new Promise(r => setTimeout(r, 4000));
    scenes.corp.classList.add('glitching');
    
    // Play glitch effect for 2s
    await new Promise(r => setTimeout(r, 2000));
    scenes.corp.classList.remove('active');
    scenes.action.classList.add('active');
    resumeSavedTimer();
}

function getSavedDeadline() {
    const savedDeadline = Number(localStorage.getItem(TIMER_STORAGE_KEY));
    if (Number.isFinite(savedDeadline) && savedDeadline > Date.now()) {
        return savedDeadline;
    }
    localStorage.removeItem(TIMER_STORAGE_KEY);
    return null;
}

function showCountdown(deadline) {
    scenes.action.classList.remove('active');
    scenes.countdown.classList.add('active');
    startTimer(deadline);
}

// 3. Action Button
document.getElementById('start-btn').addEventListener('click', () => {
    const savedDeadline = getSavedDeadline();
    const deadline = savedDeadline || Date.now() + 60 * 60 * 1000;
    localStorage.setItem(TIMER_STORAGE_KEY, String(deadline));
    showCountdown(deadline);
});

// 4. Timer Logic
function startTimer(deadline) {
    const display = document.getElementById('timer');
    const updateTimer = () => {
        const timer = Math.max(0, Math.ceil((deadline - Date.now()) / 1000));
        const hours = Math.floor(timer / 3600);
        const minutes = Math.floor((timer % 3600) / 60);
        const seconds = timer % 60;

        display.textContent =
            String(hours).padStart(2, '0') + ':' +
            String(minutes).padStart(2, '0') + ':' +
            String(seconds).padStart(2, '0');

        if (timer === 0) {
            localStorage.removeItem(TIMER_STORAGE_KEY);
        }
    };

    updateTimer();
    setInterval(() => {
        updateTimer();
    }, 1000);
}

function resumeSavedTimer() {
    const savedDeadline = getSavedDeadline();
    if (savedDeadline) {
        showCountdown(savedDeadline);
    }
}

// Start everything
window.onload = runIntro;
