# สำรวจประสิทธิภาพ SD Card สำหรับ Raspberry Pi 5 + Hailo-8

บทความนำเสนอแนวทางทดสอบ SD Card แต่ละรุ่นด้วย Benchmark Suite ใน repository นี้ เพื่อหาทางเลือกแทนการใช้การ์ดที่ pre-load official image ตามแรงบันดาลใจจากบทความของ BS4U-TECH [[1]](#ref1)

## 1. กรณีใช้งานที่เน้นวิเคราะห์

- **Edge AI / Model Deployment** – ต้องการ throughput สูง และ latency ต่ำ สำหรับโหลดโมเดลและ assets
- **Camera Vision / Continuous Recording** – ต้องการความทนทานในการเขียนซ้ำต่อเนื่อง
- **Prototype / Low Cost** – ให้ความสำคัญกับราคาย่อมเยาเพื่อทดสอบระบบ

## 2. Metrics ที่วัดได้จาก Benchmark Suite

- `sequential_write (MB/s)` – ความเร็วเขียนไฟล์ขนาดใหญ่ต่อเนื่อง
- `sequential_read (MB/s)` – ความเร็วอ่านไฟล์ขนาดใหญ่ต่อเนื่อง
- `random_read (MB/s)` – ความเร็วอ่านสุ่มด้วยบล็อกเล็ก (ค่าเฉลี่ย MB/s พร้อม IOPS)
- `random_write (MB/s)` – ความเร็วเขียนสุ่มพร้อมค่า latency

สคริปต์ `scripts/run_benchmark.py` จะบันทึกผลลัพธ์เป็นไฟล์ JSON บนเครื่องทดสอบเพื่อให้เปรียบเทียบภายหลังได้บนหลักการเดียวกันทุกการ์ด

## 3. วิธีรันทดสอบ

1. ติดตั้ง dependency: `pip install -r requirements.txt`
2. Image ระบบปฏิบัติการลงการ์ดที่ต้องการทดสอบ
3. Mount การ์ด และระบุ path ให้กับสคริปต์
4. รันคำสั่ง:
   ```
   python scripts/run_benchmark.py "SanDisk Extreme Pro MicroSDXC 64GB" D:\ --plan data/default_plan.yaml --results-dir results
   ```
5. ทำซ้ำกับการ์ดทุกตัวที่ต้องการเปรียบเทียบ

## 4. สรุปผลและนำเสนอ

เมื่อมีไฟล์ JSON ในโฟลเดอร์ `results/` แล้ว ใช้คำสั่ง:

```
python scripts/generate_report.py results --output-dir reports
```

เครื่องมือจะสร้าง:

- `reports/summary.md` – ตารางสรุปค่าเฉลี่ย throughput ของแต่ละการ์ดแยกตามประเภทการทดสอบ
- `reports/comparison.png` – กราฟแท่งเปรียบเทียบแบบรวมเพื่อใช้ในงานนำเสนอหรือบทความ

## 5. แนวทางการตีความผลลัพธ์

- ค่าความเร็วเฉลี่ย (MB/s) สูงขึ้นแปลว่าการ์ดตอบสนอง workload ได้ดีขึ้น
- ค่า IOPS และ latency ต่ำช่วยให้การรัน inference model บน Pi 5 ทำได้รวดเร็วและเสถียร
- ผสานข้อมูลราคาจาก `data/sd_cards.yaml` เพื่อพิจารณาความคุ้มค่าเมื่อเทียบกับ Official Preloaded SD Card

## 6. ข้อควรระวังในการทดสอบจริง

- ปิดโปรแกรมอื่นที่อาจรบกวน I/O ขณะทดสอบ
- ทำงานบนระบบไฟฟ้าที่เสถียรเพื่อลดโอกาสการ์ดเสียหายจากการเขียนหนัก
- ตรวจสอบอุณหภูมิและบันทึกหมายเหตุในการทดสอบแต่ละครั้ง (สามารถเพิ่มลงใน `metadata` ในไฟล์ YAML)

## อ้างอิง

<a id="ref1">[1]</a> BS4U-TECH – สำรวจและวิเคราะห์ SD Card ทางเลือกแทน Official Image. https://www.bs4u-tech.com/blog/expertise-insights-1/%E0%B8%AA%E0%B8%B2%E0%B8%A3%E0%B8%A7%E0%B8%88%E0%B9%81%E0%B8%A5%E0%B8%B0%E0%B8%A7%E0%B9%80%E0%B8%84%E0%B8%A3%E0%B8%B2%E0%B8%B0%E0%B8%AB-sd-card-%E0%B8%97%E0%B8%B2%E0%B8%87%E0%B9%80%E0%B8%A5%E0%B8%AD%E0%B8%81%E0%B9%81%E0%B8%97%E0%B8%99-official-image-8

