# Інструкція з розгортання та керування CTF

## 1. Системні вимоги
- ОС: Ubuntu 22.04 LTS / Debian 12 / Kali Linux / WSL2
- Пакети: `docker`, `docker-compose-v2`, `python3` (встановлюються автоматично через `setup.sh`)

## 2. Команди керування
- **Повний запуск (перший раз):** `./setup.sh`
- **Зупинка всього:** `docker compose down`
- **Перезапуск конкретного завдання:** `docker compose restart volyngas_ctf`
- **Перегляд логів VPN порталу:** `docker compose logs -f vpn_portal`

## 3. Як зробити щоб люди могли заходити через впн 

Зайдіть як адмін на http://localhost:8000.

Перейдіть у Admin Panel -> Pages -> All Pages -> New Page.

Назвіть сторінку VPN (Route: vpn).

Обов'язково перемкніть редактор з Visual на HTML (кнопка <>) і вставте цей код

```
<div class="container text-center mt-5">
    <h2>Доступ до CTF інфраструктури</h2>
    <p>Для вирішення завдань необхідно підключитися до нашої мережі (VPN).</p>
    
    <div class="card bg-dark border-primary p-4 mt-4 mx-auto" style="max-width: 500px;">
        <button id="downloadVpnBtn" class="btn btn-primary btn-lg mt-3">
            Завантажити OpenVPN Config
        </button>
    </div>
</div>

<script>
document.getElementById('downloadVpnBtn').addEventListener('click', function() {
    const username = window.init.user.name; 
    
    if (!username) {
        alert('Спочатку авторизуйтесь на платформі!');
        return;
    }

    this.innerText = 'Генерація ключів...';
    this.disabled = true;

    // Вкажіть тут публічний IP вашого сервера, якщо це не локалхост
    const downloadUrl = `http://localhost:5050/api/vpn/download?user=${username}`;
    
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.click();

    setTimeout(() => {
        this.innerText = 'Завантажити OpenVPN Config';
        this.disabled = false;
    }, 3000);
});
</script>
```