import cv2
import time
import numpy as np
from ultralytics import YOLO

class DefectDetector:
    def __init__(self, model_path='yolov8n.pt', source=0, simulation_mode=False):
        """
        model_path: Eğitilmiş YOLO model yolu (.pt dosyası). Yoksa 'yolov8n.pt' indirir.
        source: Kamera ID (0) veya video dosya yolu.
        simulation_mode: True ise kamera yerine rastgele hata simüle eder.
        """
        self.simulation_mode = simulation_mode
        self.source = source
        
        if not self.simulation_mode:
            print(f"Model yükleniyor: {model_path}...")
            # İlk çalıştırmada internetten indirecektir (yaklaşık 6MB)
            self.model = YOLO(model_path)
            self.cap = cv2.VideoCapture(self.source)
            if not self.cap.isOpened():
                print("Hata: Kamera açılamadı! Simülasyon moduna geçiliyor.")
                self.simulation_mode = True
        
        # Simülasyon için zamanlayıcılar
        self.last_defect_time = time.time()
        self.next_defect_interval = 2.0 # İlk hata 2 saniye sonra

    def get_frame_and_check_defect(self):
        """
        Bir frame (resim) alır ve hata olup olmadığını kontrol eder.
        Geri dönüş: (frame, defect_detected_bool, defect_info_str)
        """
        if self.simulation_mode:
            return self._simulate_defect()
        
        ret, frame = self.cap.read()
        if not ret:
            print("Kare okunamadı, video bitti mi?")
            return None, False, ""

        # YOLO ile tahmin yap
        # classes parametresi ile sadece belirli sınıflara bakılabilir.
        # Defect Detection için özel eğitilmiş modelde classes filtresine gerek olmayabilir.
        results = self.model(frame, verbose=False)
        
        defect_detected = False
        defect_info = ""
        
        # Sonuçları çiz
        annotated_frame = results[0].plot()
        
        # Tespit edilen nesneleri kontrol et
        # Eğer özel eğitilmiş modelse, conf (güvenilirlik) > 0.5 ise hata kabul et
        for r in results:
            if len(r.boxes) > 0:
                defect_detected = True
                defect_info = f"Hata Sayısı: {len(r.boxes)}"
        
        return annotated_frame, defect_detected, defect_info

    def _simulate_defect(self):
        """
        Kamera yokken testi sağlamak için yapay veri üretir.
        """
        # Siyah bir zemin oluştur
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        current_time = time.time()
        defect_detected = False
        msg = "Simulation: Searching..."
        
        # Rastgele aralıklarla "HATA" oluştur
        if current_time - self.last_defect_time > self.next_defect_interval:
            defect_detected = True
            msg = "SIMULATION: DEFECT DETECTED!"
            
            # Kırmızı bir daire çiz
            cv2.circle(frame, (320, 240), 50, (0, 0, 255), -1)
            cv2.putText(frame, "LEKE", (280, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # Reset timers
            self.last_defect_time = current_time
            self.next_defect_interval = np.random.uniform(2.0, 5.0) # 2-5 sn arası bekle
            
        else:
            # Temiz durum göstergesi (Yeşil)
            cv2.circle(frame, (50, 50), 20, (0, 255, 0), -1)
            
        cv2.putText(frame, msg, (10, 450), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # 30 FPS simülasyonu
        time.sleep(0.033)
        
        return frame, defect_detected, msg

    def release(self):
        if hasattr(self, 'cap') and self.cap:
            self.cap.release()
