import cv2
import time
from vision import DefectDetector
from plc_comms import PLCClient

def main():
    print("--- Senkronize Kumaş Hata İşaretleme Sistemi ---")
    
    # AYARLAR (Fiziki PLC)
    # S7-1200/1500 için genelde Rack=0, Slot=1 dir.
    PLC_IP = '192.168.10.200'     
    PLC_RACK = 0
    PLC_SLOT = 1
    
    DB_NUMBER = 1              # TIA Portal'da oluşturduğunuz DB numarası
    DB_BYTE = 0                # Hata sinyali byte adresi
    DB_BIT = 0                 # Hata sinyali bit adresi (Örn: DB1.DBX0.0)
    
    # 1. Vision Başlat (Gerçek Kamera)
    # model_path='yolov8n.pt' varsa onu kullanır, yoksa indirir.
    # simulation_mode=False yaptık çünkü gerçek kamera (webcam) var.
    detector = DefectDetector(model_path='yolov8n.pt', source=0, simulation_mode=False)
    
    # 2. PLC Client Başlat
    plc = PLCClient(ip=PLC_IP, rack=PLC_RACK, slot=PLC_SLOT, db_number=DB_NUMBER)
    
    # PLC Bağlantı Kontrolü (Döngüye girmeden önce)
    print(f"PLC'ye bağlanmaya çalışılıyor ({PLC_IP})...")
    plc.connect()
    
    if not plc.connected:
        print("UYARI: PLC'ye bağlanılamadı! Sistem yine de çalışacak ancak sinyal gönderilemeyecek.")
        print("Lütfen Ethernet kablosunu ve IP ayarlarını kontrol edin.")
    else:
        print("BAŞARILI: Fiziki PLC bağlantısı sağlandı.")

    print("Sistem Başlatıldı. 'q' tuşuna basarak çıkabilirsiniz.")

    try:
        while True:
            # Görüntü al ve analiz et
            frame, defect_detected, info = detector.get_frame_and_check_defect()
            
            if frame is None:
                break

            # Eğer hata tespit edildiyse
            if defect_detected:
                print(f"[{time.strftime('%H:%M:%S')}] HATA TESPİT EDİLDİ! PLC Tetikleniyor...")
                # Ekrana görsel uyarı çiz
                cv2.rectangle(frame, (0,0), (640, 50), (0,0,255), -1)
                cv2.putText(frame, "!!! HATALI URUN !!!", (200, 35), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
                
                # PLC'ye sinyal gönder
                plc.trigger_defect_signal(byte_index=DB_BYTE, bit_index=DB_BIT)
            
            if plc.connected:
                status_text = "PLC: ONLINE"
                color = (0, 255, 0)
            else:
                status_text = "PLC: OFFLINE"
                color = (0, 0, 255)
            
            cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            
            # Görüntüyü göster
            cv2.imshow("Defect Detection System", frame)

            # Çıkış
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        print("Kullanıcı tarafından durduruldu.")
    finally:
        detector.release()
        plc.disconnect()
        cv2.destroyAllWindows()
        print("Program kapandı.")

if __name__ == "__main__":
    main()
