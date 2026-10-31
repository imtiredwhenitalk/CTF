<?php
/**
 * UploadHandler — обробка завантаження відгуку пацієнта.
 *
 * [VULN] Навмисно немає:
 *   1. Перевірки MIME-типу / magic bytes файлу.
 *   2. Білого списку дозволених розширень.
 *   3. Заборони виконання скриптів у директорії завантажень
 *      (див. app/public/uploads/.htaccess).
 *
 * Це дозволяє завантажити файл з розширенням .php під виглядом
 * "скану направлення" і отримати виконання коду на сервері
 * (CWE-434, OWASP A04).
 */

final class UploadHandler
{
    private string $uploadDir;

    public function __construct(string $uploadDir)
    {
        $this->uploadDir = rtrim($uploadDir, '/').'/';
    }

    /**
     * @param array $file Один елемент $_FILES (напр. $_FILES['attachment'])
     * @return array{ok:bool, path?:string, error?:string}
     */
    public function handle(array $file): array
    {
        if (!isset($file['error']) || $file['error'] !== UPLOAD_ERR_OK) {
            return ['ok' => false, 'error' => 'Помилка завантаження файлу'];
        }

        $originalName = basename($file['name']);
        $safeBaseName = preg_replace('/[^A-Za-z0-9_.-]/', '_', $originalName);
        $destName     = uniqid('review_').'_'.$safeBaseName;
        $destPath     = $this->uploadDir.$destName;

        if (!is_dir($this->uploadDir)) {
            mkdir($this->uploadDir, 0755, true);
        }

        if (!move_uploaded_file($file['tmp_name'], $destPath)) {
            return ['ok' => false, 'error' => 'Не вдалося зберегти файл на сервері'];
        }

        return ['ok' => true, 'path' => 'uploads/'.$destName];
    }
}
