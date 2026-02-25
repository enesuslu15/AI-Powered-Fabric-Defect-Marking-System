import snap7
from snap7.util import set_bool, set_int, set_real
import time

class PLCClient:
    def __init__(self, ip='192.168.0.1', rack=0, slot=1, db_number=1):
        self.ip = ip
        self.rack = rack
        self.slot = slot
        self.db_number = db_number
        self.client = snap7.client.Client()
        self.connected = False

    def connect(self):
        try:
            if self.connected:
                self.disconnect()
            
            # Eski client nesnesini temizle ve yenisini oluştur (State hatasını önlemek için)
            if hasattr(self, 'client') and self.client:
                self.client.destroy()
            
            self.client = snap7.client.Client()
            
            print(f"PLC'ye bağlanılıyor ({self.ip})...")
            self.client.connect(self.ip, self.rack, self.slot)
            self.connected = self.client.get_connected()
            
            if self.connected:
                print("PLC Bağlantısı BAŞARILI.")
        except Exception as e:
            print(f"PLC Bağlantı Hatası: {e}")
            self.connected = False

    def trigger_defect_signal(self, byte_index=0, bit_index=0):
        """
        PLC'deki DB'de ilgili bit'i TRUE yapar, kısa bir süre sonra FALSE yapar (Pulse).
        """
        if not self.connected:
            # Yeniden bağlanmayı dene
            self.connect()
            if not self.connected: 
                return # Hala bağlı değilse çık

        try:
            # 1. Okuma (Mevcut byte'ı bozmak istemeyiz, ama sadece 1 bit değişecekse sıfırdan byte oluşturulabilir)
            # Güvenli yöntem: Oku -> Değiştir -> Yaz
            # Ancak performans için direkt yazma yapılabilir. Biz burada basitlik için sadece o byte'ı yöneteceğiz.
            
            # DB'den 1 byte oku
            data = self.client.db_read(self.db_number, byte_index, 1)
            
            # Biti TRUE Set et
            set_bool(data, 0, bit_index, True)
            self.client.db_write(self.db_number, byte_index, data)
            # print("PLC Sinyal Gönderildi: TRUE")
            
            # Çok kısa bekle ve Resetle (PLC programında Rising Edge kullanıyorsak bu gerekli olmayabilir 
            # ancak Python döngüsü yavaşsa PLC bunu sürekli 1 görebilir. 
            # En temiz yöntem: Python 1 yazar, PLC işlemi yapınca 0'a çeker (Handshake).
            # VEYA Python 1 saniyelik bir pulse üretir.)
            
            time.sleep(0.1) 
            
            set_bool(data, 0, bit_index, False)
            self.client.db_write(self.db_number, byte_index, data)
            # print("PLC Sinyal Sıfırlandı: FALSE")

        except Exception as e:
            print(f"PLC Yazma Hatası: {e}")
            self.connected = False

    def disconnect(self):
        if self.client:
            self.client.disconnect()
            self.connected = False
            print("PLC Bağlantısı kesildi.")
