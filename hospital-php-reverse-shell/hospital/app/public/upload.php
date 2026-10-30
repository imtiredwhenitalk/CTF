<?php
require __DIR__.'/../src/UploadHandler.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST' || !isset($_FILES['attachment'])) {
    header('Location: review.php?err='.urlencode('Файл не надіслано'));
    exit;
}

$handler = new UploadHandler(__DIR__.'/uploads');
$result  = $handler->handle($_FILES['attachment']);

if ($result['ok']) {
    header('Location: review.php?ok=1&f='.urlencode($result['path']));
} else {
    header('Location: review.php?err='.urlencode($result['error']));
}
exit;
