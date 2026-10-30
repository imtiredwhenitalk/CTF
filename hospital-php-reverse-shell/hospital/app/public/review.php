<!DOCTYPE html>
<html lang="uk">
<head>
<meta charset="UTF-8">
<title>Залишити відгук — МедЦентр Пульс</title>
<link rel="stylesheet" href="style.css">
</head>
<body>

<header>
  <div class="logo"><span class="cross">✚</span> МедЦентр Пульс</div>
  <nav>
    <a href="index.php">Головна</a>
    <a href="#services">Послуги</a>
    <a href="review.php">Записатися / Відгук</a>
  </nav>
</header>

<div class="container">
  <div class="card">
    <span class="badge">Відгук пацієнта</span>
    <h2>Залишити відгук про прийом</h2>

    <?php if (isset($_GET['ok'])): ?>
      <div class="msg ok">Дякуємо! Ваш відгук та прикріплений файл успішно надіслано.<br>
        Файл збережено: <code><?php echo htmlspecialchars($_GET['f'] ?? ''); ?></code>
      </div>
    <?php elseif (isset($_GET['err'])): ?>
      <div class="msg err">Помилка завантаження: <?php echo htmlspecialchars($_GET['err']); ?></div>
    <?php endif; ?>

    <form class="upload-form" action="upload.php" method="POST" enctype="multipart/form-data">
      <label>Відділення / лікар:</label>
      <input type="text" name="department" placeholder="напр. Терапевт, кабінет 4" required>

      <label>Ваш відгук:</label>
      <textarea name="text" rows="4" placeholder="Поділіться враженнями про прийом..." required></textarea>

      <label>Скан направлення або результату (jpg/png/pdf):</label>
      <input type="file" name="attachment" required>

      <button type="submit">Надіслати відгук</button>
    </form>
  </div>
</div>

<footer>© 2026 МедЦентр Пульс. Навчальний стенд (CTF).</footer>

</body>
</html>
