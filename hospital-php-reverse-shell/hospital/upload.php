<?php
$uploadDir = __DIR__ . '/uploads/';

if ($_SERVER['REQUEST_METHOD'] !== 'POST' || !isset($_FILES['attachment'])) {
    header('Location: review.php?err=' . urlencode('Файл не надіслано'));
    exit;
}

$file = $_FILES['attachment'];

if ($file['error'] !== UPLOAD_ERR_OK) {
    header('Location: review.php?err=' . urlencode('Помилка завантаження файлу'));
    exit;
}

$originalName = basename($file['name']);
$safeBaseName = preg_replace('/[^A-Za-z0-9_.-]/', '_', $originalName);
$destName     = uniqid('review_') . '_' . $safeBaseName;
$destPath     = $uploadDir . $destName;

if (!is_dir($uploadDir)) {
    mkdir($uploadDir, 0755, true);
}

if (move_uploaded_file($file['tmp_name'], $destPath)) {
    header('Location: review.php?ok=1&f=' . urlencode('uploads/' . $destName));
    exit;
} else {
    header('Location: review.php?err=' . urlencode('Не вдалося зберегти файл на сервері'));
    exit;
}
