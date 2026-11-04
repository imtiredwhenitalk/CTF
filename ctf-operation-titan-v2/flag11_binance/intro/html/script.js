const chatBox = document.getElementById('chat-box');
const scenes = {
    chat: document.getElementById('chat-container'),
    corp: document.getElementById('corp-container'),
    action: document.getElementById('action-container'),
    countdown: document.getElementById('countdown-container')
};

const script = [
    { sender: "slurr", text: "kopiko, ти тут?", delay: 1000 },
    { sender: "kopiko", text: "Так. Що трапилось?", delay: 3000 },
    { sender: "slurr", text: "Я щойно знайшов критичну діру в API Binance (v3).", delay: 2500 },
    { sender: "kopiko", text: "Ти серйозно? Це ж корпорація з мільярдними оборотами. Нас вичислять за хвилину.", delay: 4000 },
    { sender: "slurr", text: "Не вичислять, якщо зробимо все швидко. Їхній дебаг-роут забули закрити у проді.", delay: 4500 },
    { sender: "slurr", text: "Там лежать ключі доступу до Холодного Гаманця (Cold Wallet).", delay: 3000 },
    { sender: "kopiko", text: "Гаддем чувак. Це джекпот. Який план?", delay: 3500 },
    { sender: "slurr", text: "У нас є рівно 2 години, поки їхні адміни не зроблять ротацію токенів сесій.", delay: 4000 },
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
}

// 3. Action Button
document.getElementById('start-btn').addEventListener('click', () => {
    scenes.action.classList.remove('active');
    scenes.countdown.classList.add('active');
    startTimer(60 * 60); // 1 hour
});

// 4. Timer Logic
function startTimer(duration) {
    let timer = duration, hours, minutes, seconds;
    const display = document.getElementById('timer');
    setInterval(function () {
        hours = parseInt(timer / 3600, 10);
        minutes = parseInt((timer % 3600) / 60, 10);
        seconds = parseInt(timer % 60, 10);

        hours = hours < 10 ? "0" + hours : hours;
        minutes = minutes < 10 ? "0" + minutes : minutes;
        seconds = seconds < 10 ? "0" + seconds : seconds;

        display.textContent = hours + ":" + minutes + ":" + seconds;
        if (--timer < 0) timer = 0;
    }, 1000);
}

// Start everything
window.onload = runIntro;
