# Quad Robot Leg Project

Bu projeyi, bir **quad robot bacağı** için hazırladık

## Klasörler ve İçerikler:

### 1. `leg_driver`
- Arduino kodlarını içeriyor.
- Bağlı olan bileşenler:
  - Bir ekran (Arduino üzerinde bilgi görüntülemek için).
  - **Potansiyometre** (motor hızını kontrol etmek için).
  - **Victor SPX motor sürücü** (motor sürmek için).
  - **Encoder** (geri bildirim almak için).

### 2. `scripts`
- `theoretical.py`: Teorik değerleri hafif jitter ekleyerek hesaplayan bir Python scripti.
- Çıktıları dosyaya kaydediyo, potansiyel testler ve analizler için kullanılabilir.


### Hesaplar
python teorik hesaplama dosyasına bakman lazım, hiçbir hesapta lead screw forceundan ileri gitmedim. 
bacağın ucunda uygulanacak tork işini yapabilecek vakit ve bilgimin olduğunu sanmıyorum. 

### Jitter
değerlere uyguladığım jitter bi tık fazla kaçmış olabilir onla oynayabilirsin apply_jitter(value, jitter_percentage)
tarzında kullandım, percentage azaltırsın istersen

### grafik
grafiklerde jitter uygulanmış noktaları yumuşatmak için moving average, gaussian ve adını unuttğum 2 şey daha denedim
bence en güzeli gaussian ama beğenmezsen data pointleri alıp matlabde istediğin gibi değiştirebilirsin

