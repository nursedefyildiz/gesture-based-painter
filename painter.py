import cv2
import numpy as np
import mediapipe.python.solutions.hands as mp_hands

# --- TEMEL AYARLAR ---
cap = cv2.VideoCapture(0)
cap.set(3, 1280) # Genişlik
cap.set(4, 720)  # Yükseklik

# Çizimlerin yapılacağı boş siyah tuval
canvas = np.zeros((720, 1280, 3), np.uint8)

px, py = 0, 0
drawColor = (255, 180, 220) # Başlangıç: Lila
brushThickness = 8
brushType = "daire"

#  Renk Paleti (BGR formatında)
colors = [
    {"name": "Lila", "color": (255, 180, 220), "center": (350, 60)}, 
    {"name": "Pembe", "color": (180, 180, 255), "center": (430, 60)}, 
    {"name": "Su Yesili", "color": (200, 255, 180), "center": (510, 60)}, 
    {"name": "Acik Sari", "color": (180, 255, 255), "center": (590, 60)}, 
    {"name": "Turuncu", "color": (150, 200, 255), "center": (670, 60)}, 
    {"name": "Beyaz", "color": (240, 240, 240), "center": (750, 60)}, 
    {"name": "Silgi", "color": (40, 40, 40), "center": (830, 60)}      
]

# Fırça Tipleri
brushes = [
    {"type": "daire", "center": (950, 60)},
    {"type": "kare", "center": (1020, 60)},
    {"type": "sprey", "center": (1090, 60)}
]

hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.85)

def draw_studio_ui(img, current_color, current_thickness, current_type):
    # Üst Menü Paneli 
    overlay = img.copy()
    cv2.rectangle(overlay, (300, 15), (1150, 105), (255, 255, 255), cv2.FILLED)
    # Sağ Kalınlık Paneli
    cv2.rectangle(overlay, (1210, 150), (1270, 570), (255, 255, 255), cv2.FILLED)
    cv2.addWeighted(overlay, 0.2, img, 0.8, 0, img)
    
    # Renk Daireleri
    for item in colors:
        cx, cy = item["center"]
        is_selected = (item["color"] == current_color)
        cv2.circle(img, (cx, cy), 25, item["color"], cv2.FILLED)
        if is_selected:
            cv2.circle(img, (cx, cy), 32, (255, 255, 255), 2)

    # Fırça İkonları
    for b in brushes:
        bx, by = b["center"]
        is_b_selected = (b["type"] == current_type)
        c = (50, 50, 50) if is_b_selected else (180, 180, 180)
        if b["type"] == "daire": cv2.circle(img, (bx, by), 12, c, 2)
        elif b["type"] == "kare": cv2.rectangle(img, (bx-10, by-10), (bx+10, by+10), c, 2)
        elif b["type"] == "sprey": cv2.circle(img, (bx, by), 2, c, cv2.FILLED); cv2.circle(img, (bx+4, by+4), 2, c, cv2.FILLED)
        if is_b_selected: cv2.rectangle(img, (bx-20, by-20), (bx+20, by+20), (100, 100, 100), 1)

    # Kalınlık Barı
    vol_bar = np.interp(current_thickness, [2, 50], [550, 170])
    cv2.rectangle(img, (1230, 170), (1250, 550), (200, 200, 200), 2)
    cv2.rectangle(img, (1230, int(vol_bar)), (1250, 550), current_color, cv2.FILLED)
    cv2.putText(img, f"{current_thickness}", (1220, 600), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

while True:
    success, img = cap.read()
    if not success: break
    img = cv2.flip(img, 1)

    # 1. UI Çizimi
    draw_studio_ui(img, drawColor, brushThickness, brushType)

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)

    # El verilerini işlemeden önce x1, y1 değerlerini tanımlayalım
    x1, y1 = 0, 0

    if results.multi_hand_landmarks:
        for hand_lms in results.multi_hand_landmarks:
            landmarks = hand_lms.landmark
            h, w, c = img.shape
            
            # Parmak uçlarını kontrol et
            fingers = []
            # Baş parmak (4)
            if landmarks[4].x < landmarks[3].x: fingers.append(1)
            else: fingers.append(0)
            # Diğer 4 parmak (8, 12, 16, 20)
            for id in [8, 12, 16, 20]:
                if landmarks[id].y < landmarks[id-2].y: fingers.append(1)
                else: fingers.append(0)

            x1, y1 = int(landmarks[8].x * w), int(landmarks[8].y * h)
            x2, y2 = int(landmarks[12].x * w), int(landmarks[12].y * h)

            # --- GESTURE KONTROLLERİ ---
            
            # A. TEMİZLE: Sadece Serçe Parmak Havada
            if fingers == [0, 0, 0, 0, 1]:
                canvas = np.zeros_like(canvas)
                px, py = 0, 0

            # B. SEÇİM VE AYAR: İşaret + Orta Parmak Havada
            elif fingers[1] == 1 and fingers[2] == 1:
                px, py = 0, 0
                # Üst Menü (Renk/Fırça Seçimi)
                if y1 < 120:
                    for item in colors:
                        cx, cy = item["center"]
                        if abs(x1 - cx) < 30: drawColor = item["color"]
                    for b in brushes:
                        bx, by = b["center"]
                        if abs(x1 - bx) < 30: brushType = b["type"]
                # Sağ Bar (Kalınlık Ayarı)
                if x1 > 1200:
                    brushThickness = int(np.interp(y1, [170, 550], [50, 2]))

            # C. ÇİZİM: Sadece İşaret Parmağı Havada
            elif fingers[1] == 1 and fingers[2] == 0:
                if px == 0 and py == 0: px, py = x1, y1
                
                # Silgi ise siyah boya (arka plan rengi)
                actual_color = (0, 0, 0) if drawColor == (40, 40, 40) else drawColor
                
                if brushType == "daire":
                    cv2.line(canvas, (px, py), (x1, y1), actual_color, brushThickness)
                elif brushType == "kare":
                    cv2.rectangle(canvas, (x1-brushThickness, y1-brushThickness), 
                                  (x1+brushThickness, y1+brushThickness), actual_color, cv2.FILLED)
                elif brushType == "sprey":
                    for _ in range(8):
                        rx, ry = np.random.randint(-brushThickness*2, brushThickness*2, 2)
                        cv2.circle(canvas, (x1+rx, y1+ry), 1, actual_color, cv2.FILLED)
                
                px, py = x1, y1
            else:
                px, py = 0, 0

    # --- KATMAN BİRLEŞTİRME  ---
    # Çizimleri kameraya ekle
    imgGray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
    _, imgInv = cv2.threshold(imgGray, 10, 255, cv2.THRESH_BINARY_INV)
    imgInv = cv2.cvtColor(imgInv, cv2.COLOR_GRAY2BGR)
    img = cv2.bitwise_and(img, imgInv)
    img = cv2.bitwise_or(img, canvas)

    # İmleci Çizimin Üstüne Koyma
    if x1 != 0 and y1 != 0:
        cv2.circle(img, (x1, y1), brushThickness + 2, (255, 255, 255), 2)
        cv2.circle(img, (x1, y1), brushThickness, drawColor, cv2.FILLED)

    cv2.imshow("Sanal Ressam v1.0", img)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()