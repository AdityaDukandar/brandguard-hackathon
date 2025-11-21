# 🛡️ BrandGuard: The Fake App Detector

> **Winner/Project for [Hackathon Name]**
> *Protecting users and brands from malicious clones in < 30 seconds.*

## 🚨 The Problem
Fake apps steal **$4B+ annually** in user data and brand revenue.
Identifying them usually requires:
* Expensive legal teams ❌
* Manual APK reverse engineering ❌
* Days of analysis ❌

## ⚡ The Solution: BrandGuard
BrandGuard is an **AI-powered automated defense system** that:
1.  **Scans APKs** instantly (Metadata, Icons, Permissions).
2.  **Detects Clones** using Computer Vision (CLIP) & Text Similarity (Levenshtein).
3.  **Auto-Generates Legal Evidence**, drafting a takedown request PDF in seconds.

---

## 🎥 Demo
[Link to Demo Video - TBD]

## 📸 Screenshots
*(Add a screenshot of your UI here later)*

---

## 🛠️ Tech Stack
* **Frontend:** HTML5 / Bootstrap / Jinja2
* **Backend:** Python / FastAPI
* **Analysis Engine:** * `androguard` (APK Metadata extraction)
    * `thefuzz` (Text similarity scoring)
    * `imagehash` (Icon visual matching)
* **Reporting:** `reportlab` (PDF Generation)

---

## 🚀 How to Run Locally

### 1. Clone the Repo
```bash
git clone [https://github.com/AdityaDukandar/brandguard-hackathon.git](https://github.com/AdityaDukandar/brandguard-hackathon.git)
cd brandguard-hackathon
