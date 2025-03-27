<?php
$update = file_get_contents("php://input");
$url = "http://localhost:8080"; // این آدرس رو بعداً با آدرس ngrok جایگزین می‌کنی
$ch = curl_init($url);
curl_setopt($ch, CURLOPT_POST, 1);
curl_setopt($ch, CURLOPT_POSTFIELDS, $update);
curl_setopt($ch, CURLOPT_HTTPHEADER, array('Content-Type: application/json'));
curl_exec($ch);
curl_close($ch);
?>