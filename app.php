<?php
$message = "";
$status = "";

$limit_file = 'limits.json';
$cooldown_seconds = 24 * 60 * 60; 
$user_ip = $_SERVER['REMOTE_ADDR']; 

$limits = [];
if (file_exists($limit_file)) {
    $limits = json_decode(file_get_contents($limit_file), true) ?: [];
}

if ($_SERVER["REQUEST_METHOD"] == "POST") {
    $service = filter_input(INPUT_POST, 'service', FILTER_SANITIZE_STRING);
    $target_url = filter_input(INPUT_POST, 'target_url', FILTER_SANITIZE_URL);
    
    if (empty($service)) {
        $status = "error";
        $message = "يرجى اختيار خدمة من البطاقات أعلاه.";
    } else {
        $last_used = isset($limits[$user_ip][$service]) ? $limits[$user_ip][$service] : 0;
        $time_passed = time() - $last_used;

        if ($time_passed < $cooldown_seconds) {
            $remaining_seconds = $cooldown_seconds - $time_passed;
            $hours = floor($remaining_seconds / 3600);
            $minutes = floor(($remaining_seconds % 3600) / 60);
            
            $status = "error";
            $message = "عذراً، لقد استخدمت هذه الخدمة. يرجى الانتظار <b>$hours ساعة و $minutes دقيقة</b>.";
        } else {
            // التوكنات الوهمية (استبدلها بحسابك الحقيقي)
            $token = "FAKETOKEN";
            $cookie = "cf_clearance=FAKECOOKIE; token=FAKETOKEN";
            $user_agent = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36";

            $api_url = "";
            $data = [];
            $referer = "";

            switch ($service) {
                case "1":
                    $api_url = "https://leofame.com/free-youtube-likes?api=1";
                    $referer = "https://leofame.com/free-youtube-likes";
                    $data = ["token" => $token, "timezone_offset" => "Asia/Baghdad", "free_link" => $target_url];
                    break;
                case "2":
                    $api_url = "https://leofame.com/free-tiktok-likes?api=1";
                    $referer = "https://leofame.com/free-tiktok-likes";
                    $data = ["token" => $token, "timezone_offset" => "Asia/Baghdad", "free_link" => $target_url];
                    break;
                case "3":
                    $api_url = "https://leofame.com/free-instagram-saves?api=1";
                    $referer = "https://leofame.com/free-instagram-saves";
                    $data = ["token" => $token, "timezone_offset" => "Asia/Baghdad", "free_link" => $target_url, "quantity" => "30", "speed" => "-1"];
                    break;
                case "4":
                    $api_url = "https://leofame.com/ar/free-tiktok-views?api=1";
                    $referer = "https://leofame.com/ar/free-tiktok-views";
                    $data = ["token" => $token, "timezone_offset" => "Asia/Baghdad", "free_link" => $target_url, "quantity" => "200"];
                    break;
            }

            if (!empty($api_url)) {
                $ch = curl_init();
                curl_setopt($ch, CURLOPT_URL, $api_url);
                curl_setopt($ch, CURLOPT_POST, true);
                curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query($data));
                curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
                
                $headers = [
                    "Host: leofame.com",
                    "sec-ch-ua-platform: \"Android\"",
                    "sec-ch-ua-mobile: ?1",
                    "User-Agent: " . $user_agent,
                    "Content-Type: application/x-www-form-urlencoded",
                    "Origin: https://leofame.com",
                    "Referer: " . $referer,
                    "Cookie: " . $cookie
                ];
                curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
                curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);

                $response = curl_exec($ch);
                $error = curl_error($ch);
                curl_close($ch);

                if ($error) {
                    $status = "error";
                    $message = "حدث خطأ في الاتصال بالخادم.";
                } elseif (strpos($response, 'Please wait') !== false || strpos($response, '"error":') !== false) {
                    $status = "error";
                    $message = "حدث خطأ من المصدر، تأكد من الرابط أو التوكن.";
                } else {
                    $status = "success";
                    $message = "تم إرسال الرشق بنجاح! جاري التنفيذ.";
                    
                    $limits[$user_ip][$service] = time();
                    file_put_contents($limit_file, json_encode($limits));
                }
            }
        }
    }
}
?>

<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Eten VIP | رشق خدمات</title>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            /* تعديل الألوان لتكون أسود داكن مع أزرق نيون */
            --bg-gradient: linear-gradient(135deg, #050505 0%, #0d0e15 100%);
            --blue-primary: #00d2ff;
            --blue-hover: #0072ff;
            --glass-bg: rgba(15, 15, 20, 0.85);
            --glass-border: rgba(0, 210, 255, 0.2);
            --text-light: #ffffff;
            --text-muted: #8b95a5;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Tajawal', sans-serif;
            background: var(--bg-gradient);
            color: var(--text-light);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }

        .vip-container {
            background: var(--glass-bg);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
            border-radius: 24px;
            padding: 40px;
            width: 100%;
            max-width: 500px;
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.8), inset 0 0 0 1px rgba(0, 210, 255, 0.05);
            text-align: center;
            position: relative;
            overflow: hidden;
        }

        /* تأثير إضاءة خفيفة في زاوية المربع */
        .vip-container::before {
            content: '';
            position: absolute;
            top: -50px;
            right: -50px;
            width: 150px;
            height: 150px;
            background: var(--blue-primary);
            filter: blur(100px);
            opacity: 0.2;
            z-index: -1;
        }

        .logo-area {
            margin-bottom: 30px;
        }

        .logo-area h1 {
            font-size: 38px;
            font-weight: 900;
            background: linear-gradient(to right, #0072ff, #00d2ff);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            letter-spacing: 4px;
            margin-bottom: 5px;
            text-shadow: 0 0 20px rgba(0, 210, 255, 0.3);
        }

        .logo-area p {
            color: var(--blue-primary);
            font-size: 14px;
            letter-spacing: 2px;
            text-transform: uppercase;
        }

        /* تصميم شبكة الخدمات (Cards) */
        .services-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-bottom: 25px;
        }

        .service-option input[type="radio"] {
            display: none;
        }

        .service-card {
            background: rgba(0, 0, 0, 0.5);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 16px;
            padding: 20px 10px;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
        }

        .service-card i {
            font-size: 30px;
            margin-bottom: 10px;
            color: var(--text-muted);
            transition: all 0.3s ease;
        }

        .service-card span {
            font-size: 14px;
            font-weight: 700;
            color: var(--text-muted);
            transition: all 0.3s ease;
        }

        /* تأثيرات عند اختيار الخدمة (أزرق) */
        .service-option input[type="radio"]:checked + .service-card {
            background: rgba(0, 210, 255, 0.08);
            border-color: var(--blue-primary);
            box-shadow: 0 0 20px rgba(0, 210, 255, 0.25);
            transform: translateY(-3px);
        }

        .service-option input[type="radio"]:checked + .service-card i,
        .service-option input[type="radio"]:checked + .service-card span {
            color: var(--blue-primary);
            text-shadow: 0 0 10px rgba(0, 210, 255, 0.5);
        }

        .service-card:hover {
            border-color: rgba(0, 210, 255, 0.3);
            background: rgba(255, 255, 255, 0.02);
        }

        /* حقل الإدخال */
        .input-group {
            position: relative;
            margin-bottom: 30px;
        }

        .input-group i {
            position: absolute;
            right: 15px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--blue-primary);
            font-size: 18px;
        }

        .input-group input {
            width: 100%;
            padding: 16px 45px 16px 15px;
            background: rgba(0, 0, 0, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            color: #fff;
            font-size: 15px;
            font-family: 'Tajawal', sans-serif;
            transition: all 0.3s ease;
        }

        .input-group input:focus {
            outline: none;
            border-color: var(--blue-primary);
            box-shadow: 0 0 15px rgba(0, 210, 255, 0.2);
        }

        /* زر الإرسال مع الإضاءة الزرقاء (Glow) */
        .submit-btn {
            width: 100%;
            padding: 18px;
            background: linear-gradient(45deg, var(--blue-hover), var(--blue-primary));
            border: none;
            border-radius: 12px;
            color: #ffffff;
            font-size: 18px;
            font-weight: 900;
            font-family: 'Tajawal', sans-serif;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            /* الإضاءة الزرقاء خلف الزر */
            box-shadow: 0 0 20px rgba(0, 210, 255, 0.5);
            position: relative;
            overflow: hidden;
            z-index: 1;
        }

        .submit-btn i {
            margin-left: 8px;
        }

        .submit-btn:hover {
            transform: translateY(-2px);
            /* زيادة التوهج عند تمرير الماوس */
            box-shadow: 0 0 35px rgba(0, 210, 255, 0.8);
            filter: brightness(1.1);
        }

        /* رسائل التنبيه */
        .alert {
            padding: 15px;
            border-radius: 12px;
            margin-bottom: 20px;
            font-size: 14px;
            font-weight: 700;
            display: <?php echo empty($message) ? 'none' : 'block'; ?>;
            animation: fadeIn 0.5s ease;
        }

        .alert.success {
            background: rgba(46, 204, 113, 0.1);
            border: 1px solid #2ecc71;
            color: #2ecc71;
            box-shadow: 0 0 15px rgba(46, 204, 113, 0.2);
        }

        .alert.error {
            background: rgba(231, 76, 60, 0.1);
            border: 1px solid #e74c3c;
            color: #e74c3c;
            box-shadow: 0 0 15px rgba(231, 76, 60, 0.2);
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* تجاوب الشاشات الصغيرة */
        @media (max-width: 400px) {
            .services-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>

<div class="vip-container">
    <div class="logo-area">
        <h1>Eten01</h1>
        <p><i class="fa-solid fa-bolt"></i>خدمات رشق</p>
    </div>
    
    <div class="alert <?php echo $status; ?>">
        <?php echo $message; ?>
    </div>

    <form method="POST" action="">
        
        <div class="services-grid">
            <label class="service-option">
                <input type="radio" name="service" value="1" required>
                <div class="service-card">
                    <i class="fa-brands fa-youtube"></i>
                    <span>يوتيوب - تفاعل</span>
                </div>
            </label>

            <label class="service-option">
                <input type="radio" name="service" value="2">
                <div class="service-card">
                    <i class="fa-brands fa-tiktok"></i>
                    <span>تيك توك - إعجابات</span>
                </div>
            </label>

            <label class="service-option">
                <input type="radio" name="service" value="3">
                <div class="service-card">
                    <i class="fa-brands fa-instagram"></i>
                    <span>إنستغرام - حفظ</span>
                </div>
            </label>

            <label class="service-option">
                <input type="radio" name="service" value="4">
                <div class="service-card">
                    <i class="fa-solid fa-eye"></i>
                    <span>تيك توك - مشاهدات</span>
                </div>
            </label>
        </div>

        <div class="input-group">
            <i class="fa-solid fa-link"></i>
            <input type="url" name="target_url" placeholder="قم بلصق الرابط هنا..." required>
        </div>

        <button type="submit" class="submit-btn"><i class="fa-solid fa-rocket"></i> إرسـال الرشـق</button>
    </form>
</div>

</body>
</html>
