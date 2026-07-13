# Tom Tat De Tai: Healthcare Text-to-SQL bang Giai Phap NLP

## 1. Dau Vao La Gi?

Dau vao cua de tai gom 2 phan chinh:

1. **Dataset y te dang CSV**
2. **Cau hoi ngon ngu tu nhien cua nguoi dung**

### Dataset

Dataset hien tai la tap cac file CSV ve du lieu y te, nam trong thu muc:

```text
data/synthea_csv
```

Trong MVP, de tai su dung cac bang chinh:

| Bang | Y nghia | So dong |
|---|---|---:|
| `patients` | Thong tin benh nhan | 11,379 |
| `encounters` | Luot kham/tuong tac y te | 656,915 |
| `conditions` | Chan doan/benh | 406,115 |
| `medications` | Thuoc duoc ke/su dung | 545,439 |
| `observations` | Chi so lam sang, xet nghiem, vital signs | 8,430,610 |
| `procedures` | Thu thuat/quy trinh dieu tri | 1,811,160 |
| `claims` | Du lieu claim/billing | 1,202,354 |
| `providers` | Thong tin provider/bac si | 1,140 |
| `organizations` | Co so y te/benh vien/phong kham | 1,140 |
| `payers` | Bao hiem/ben chi tra | 10 |

### Mau Dataset

Vi du mot so cot trong cac bang chinh:

**patients**

```text
Id, BIRTHDATE, DEATHDATE, FIRST, LAST, GENDER, CITY, STATE, HEALTHCARE_EXPENSES, HEALTHCARE_COVERAGE, INCOME
```

**encounters**

```text
Id, START, STOP, PATIENT, ORGANIZATION, PROVIDER, PAYER, ENCOUNTERCLASS, DESCRIPTION, TOTAL_CLAIM_COST
```

**conditions**

```text
START, STOP, PATIENT, ENCOUNTER, CODE, DESCRIPTION
```

**observations**

```text
DATE, PATIENT, ENCOUNTER, CATEGORY, CODE, DESCRIPTION, VALUE, UNITS, TYPE
```

### Cau Hoi Dau Vao

Nguoi dung co the nhap cau hoi bang ngon ngu tu nhien, vi du:

```text
Co bao nhieu benh nhan trong he thong?
Top 10 benh pho bien nhat la gi?
Co bao nhieu benh nhan bi Diabetes?
So luot kham theo tung nam la bao nhieu?
Chi phi claim trung binh theo tung loai encounter la bao nhieu?
```

## 2. Dau Ra La Gi?

Dau ra cua he thong la:

1. Cau SQL duoc sinh tu cau hoi tu nhien.
2. Ket qua truy van tu PostgreSQL.
3. Bang ket qua de nguoi dung doc duoc.
4. Giai thich ngan gon ve ket qua.

Vi du:

**Input**

```text
Top 10 benh pho bien nhat la gi?
```

**Generated SQL**

```sql
SELECT description, COUNT(*) AS total
FROM conditions
GROUP BY description
ORDER BY total DESC
LIMIT 10;
```

**Output**

```json
{
  "question": "Top 10 benh pho bien nhat la gi?",
  "sql": "SELECT description, COUNT(*) AS total FROM conditions GROUP BY description ORDER BY total DESC LIMIT 10;",
  "rows": [
    {
      "description": "Medication review due (situation)",
      "total": 81087
    }
  ],
  "explanation": "Truy van nhom cac chan doan theo ten benh va dem so lan xuat hien cua tung benh."
}
```

## 3. Muc Tieu De Tai

Muc tieu cua de tai la xay dung mot he thong **Healthcare Text-to-SQL Assistant** cho phep nguoi dung khai thac du lieu y te ma khong can biet SQL.

Cu the, he thong can:

- Nhan cau hoi bang ngon ngu tu nhien.
- Hieu y dinh truy van cua nguoi dung.
- Chuyen cau hoi thanh cau lenh SQL hop le.
- Kiem tra SQL de dam bao an toan.
- Truy van PostgreSQL.
- Tra ve ket qua phan tich du lieu y te.

Y nghia cua de tai:

- Giam phu thuoc vao nguoi viet SQL.
- Ho tro nguoi dung nghiep vu truy van du lieu nhanh hon.
- Ung dung NLP/LLM vao bai toan phan tich du lieu co cau truc.
- Co the danh gia bang ket qua truy van thuc te, khong chi dung o chatbot.

## 4. Thuc Hien Nhu The Nao: Giai Phap NLP

De tai su dung giai phap NLP theo huong **Text-to-SQL**.

Text-to-SQL la bai toan chuyen doi cau hoi ngon ngu tu nhien thanh cau lenh SQL.

### Luong Xu Ly

```text
Cau hoi tu nhien
-> Tien xu ly cau hoi
-> Lay schema database lien quan
-> Tao prompt cho LLM
-> LLM sinh SQL
-> Validate SQL
-> Chay SQL tren PostgreSQL
-> Tra ket qua va giai thich
```

### Thanh Phan NLP Chinh

#### 1. Natural Language Understanding

He thong can hieu cau hoi nguoi dung dang hoi ve cai gi:

- Hoi so luong: `co bao nhieu`, `count`.
- Hoi top N: `top 10`, `nhieu nhat`, `pho bien nhat`.
- Hoi theo thoi gian: `theo nam`, `trong nam 2026`, `theo thang`.
- Hoi theo nhom: `theo gioi tinh`, `theo payer`, `theo encounter class`.
- Hoi can join bang: benh theo gioi tinh, chi phi theo provider, encounter theo organization.

#### 2. Schema Linking

He thong can lien ket tu trong cau hoi voi bang/cot trong database.

Vi du:

| Tu/cum tu trong cau hoi | Bang/cot lien quan |
|---|---|
| benh, chan doan, diagnosis | `conditions.description` |
| benh nhan | `patients.id` |
| gioi tinh | `patients.gender` |
| luot kham, encounter | `encounters` |
| thuoc | `medications.description` |
| chi phi claim | `encounters.total_claim_cost` hoac `claims.outstanding1` |
| chi so, xet nghiem | `observations` |

#### 3. Prompt-Based Text-to-SQL

Ban dau, he thong dung prompt de dua schema va cau hoi cho LLM.

Vi du prompt:

```text
You are a healthcare Text-to-SQL assistant.
Generate one safe PostgreSQL SELECT query.

Schema:
patients(id, gender, city, state)
conditions(patient, description, start)

Question:
Co bao nhieu benh nhan bi Diabetes?

SQL:
```

Ket qua mong muon:

```sql
SELECT COUNT(DISTINCT patient) AS total_patients
FROM conditions
WHERE description ILIKE '%diabetes%';
```

#### 4. SQL Validation

SQL do model sinh ra khong duoc chay truc tiep. Can validate truoc:

- Chi cho phep `SELECT`.
- Chan `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, `TRUNCATE`.
- Chan nhieu statement trong mot request.
- Kiem tra bang/cot co ton tai.
- Them `LIMIT` mac dinh cho truy van tra nhieu dong.
- Dung database user read-only.

#### 5. Fine-Tuning Neu Can

Sau khi baseline chay duoc, co the fine-tune LLM bang tap du lieu:

```text
schema + natural language question -> SQL
```

Mau du lieu fine-tune:

```json
{
  "instruction": "Generate PostgreSQL SQL from the healthcare question and schema. Return only SQL.",
  "schema": "patients(id, gender), conditions(patient, description, start)",
  "question": "Top 10 benh pho bien nhat la gi?",
  "sql": "SELECT description, COUNT(*) AS total FROM conditions GROUP BY description ORDER BY total DESC LIMIT 10;"
}
```

## 5. Minh Chung Giai Phap Hieu Qua

De chung minh giai phap NLP/Text-to-SQL hieu qua, de tai khong chi danh gia cau SQL giong dap an hay khong, ma danh gia bang viec **SQL co chay dung va tra ve ket qua dung hay khong**.

### Cach Danh Gia

Tao tap test gom cac cap:

```text
cau hoi tu nhien -> SQL dung
```

Sau do so sanh SQL do he thong sinh ra voi SQL dung theo cac tieu chi:

| Chi so | Y nghia |
|---|---|
| Execution accuracy | SQL sinh ra co chay va tra ve ket qua dung khong |
| Syntax error rate | Ty le SQL bi loi cu phap |
| Schema error rate | Ty le SQL dung sai ten bang/cot |
| Safety violation rate | Ty le SQL vi pham an toan |
| Latency | Thoi gian tu cau hoi den ket qua |
| Successful query rate | Ty le cau hoi duoc tra loi thanh cong |

Chi so quan trong nhat la **Execution accuracy**.

Ly do: cung mot cau hoi co the co nhieu cau SQL khac nhau nhung van tra ve ket qua dung.

Vi du:

```sql
SELECT COUNT(*) FROM patients;
```

va:

```sql
SELECT COUNT(id) FROM patients;
```

co the deu dung neu `id` khong null.

### Bo Cau Hoi Danh Gia Mau

Nen danh gia tren nhieu nhom cau hoi:

| Nhom cau hoi | Vi du |
|---|---|
| COUNT | Co bao nhieu benh nhan? |
| GROUP BY | Co bao nhieu benh nhan theo gioi tinh? |
| TOP N | Top 10 benh pho bien nhat la gi? |
| DATE FILTER | So luot kham theo tung nam la bao nhieu? |
| JOIN 2 bang | Top benh theo gioi tinh la gi? |
| COST ANALYTICS | Chi phi claim trung binh theo encounter class la bao nhieu? |
| OBSERVATION | Chi so BMI trung binh la bao nhieu? |

### Minh Chung Bang Ket Qua Da Co

Database da import thanh cong 10 bang MVP:

| Bang | So dong |
|---|---:|
| `patients` | 11,379 |
| `encounters` | 656,915 |
| `conditions` | 406,115 |
| `medications` | 545,439 |
| `observations` | 8,430,610 |
| `procedures` | 1,811,160 |
| `claims` | 1,202,354 |
| `providers` | 1,140 |
| `organizations` | 1,140 |
| `payers` | 10 |

Mot so SQL mau da chay duoc tren PostgreSQL:

```sql
SELECT COUNT(*) AS total_patients
FROM patients;
```

Ket qua:

```text
11379
```

```sql
SELECT gender, COUNT(*) AS total
FROM patients
GROUP BY gender
ORDER BY total DESC;
```

Ket qua:

```text
M: 5748
F: 5631
```

```sql
SELECT encounterclass, COUNT(*) AS total_encounters
FROM encounters
GROUP BY encounterclass
ORDER BY total_encounters DESC;
```

Ket qua:

```text
ambulatory: 361258
wellness: 138088
outpatient: 84545
urgentcare: 29621
emergency: 25519
```

Dieu nay chung minh rang:

- Dataset da duoc import thanh cong vao database.
- Cac bang co the truy van bang SQL.
- Cac cau hoi phan tich co the anh xa thanh SQL.
- Bai toan phu hop de ap dung NLP Text-to-SQL.

## 6. Ket Luan

De tai tap trung vao bai toan ung dung NLP trong khai thac du lieu y te co cau truc.

Tom tat:

```text
Dau vao: healthcare CSV dataset + cau hoi ngon ngu tu nhien
Dau ra: SQL an toan + ket qua truy van + giai thich
Giai phap: NLP Text-to-SQL dung LLM, schema linking, prompt engineering, SQL validation
Minh chung: danh gia bang execution accuracy va ket qua truy van thuc te tren PostgreSQL
```

Gia tri chinh cua de tai la bien cau hoi tu nhien cua nguoi dung thanh truy van SQL co the chay tren database that, giup nguoi khong biet SQL van khai thac du lieu y te duoc.
