from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import requests
import pdfplumber
import os

os.makedirs("pdfs", exist_ok=True)

options = webdriver.ChromeOptions()
# options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

url = "https://www.developmentaid.org/tenders/search?showAdvancedFilters=1&all=1&ownPosts=0&locations=3,4,7&locationsIsStrict=1"
driver.get(url)
try:
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "cookie-policy-notification__close-button"))
    ).click()
    print("🍪 Cookies aceptadas automáticamente.")
except:
    print("⚠️ No se encontró el botón de cookies (quizás ya estaba oculto).")

try:
    WebDriverWait(driver, 45).until(
        EC.presence_of_element_located((By.CLASS_NAME, "tender-list-item"))
    )
    print("✅ Los elementos de licitación se cargaron correctamente.")
except:
    print("❌ Timeout: No se encontraron elementos con clase 'tender-list-item'.")

html = driver.page_source
with open("pagina_cargada.html", "w", encoding="utf-8") as f:
    f.write(driver.page_source)
driver.quit()

soup = BeautifulSoup(html, 'html.parser')
tenders = soup.find_all('div', class_='tender-list-item')
print(f"🔍 Tenders encontrados: {len(tenders)}")

for tender in tenders:
    title_tag = tender.find('a', class_='tender-title')
    title = title_tag.get_text(strip=True) if title_tag else 'Sin título'
    detail_url = "https://www.developmentaid.org" + title_tag['href'] if title_tag else None

    location = tender.find('div', class_='tender-location')
    deadline = tender.find('div', class_='tender-deadline')
    agency = tender.find('div', class_='tender-funding-agency')

    print(f"\n📌 {title}")
    print(f"   🏢 Agencia: {agency.text.strip() if agency else 'N/A'}")
    print(f"   🌍 País: {location.text.strip() if location else 'N/A'}")
    print(f"   📅 Deadline: {deadline.text.strip() if deadline else 'N/A'}")

    if tender.find('span', class_='icon-attachment'):
        print("   📎 Tiene adjunto (PDF), intentando descargar...")

        detail_resp = requests.get(detail_url)
        detail_soup = BeautifulSoup(detail_resp.text, 'html.parser')
        pdf_links = detail_soup.find_all('a', href=True)

        for link in pdf_links:
            href = link['href']
            if href.endswith('.pdf'):
                pdf_url = href if href.startswith('http') else "https://www.developmentaid.org" + href
                pdf_name = pdf_url.split('/')[-1]
                pdf_path = os.path.join('pdfs', pdf_name)

                print(f"   🔽 Descargando {pdf_name}")
                pdf_resp = requests.get(pdf_url)
                with open(pdf_path, 'wb') as f:
                    f.write(pdf_resp.content)

                print(f"   📄 Extrayendo texto de {pdf_name}...\n")
                with pdfplumber.open(pdf_path) as pdf:
                    for page_number, page in enumerate(pdf.pages, start=1):
                        text = page.extract_text()
                        if text:
                            print(f"   Página {page_number}:\n{text[:500]}...\n")
                        else:
                            print(f"   Página {page_number} vacía o no legible.")
                break
    else:
        print("   ❌ Sin adjunto (PDF)")