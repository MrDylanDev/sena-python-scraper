import os
import time
from dotenv import load_dotenv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

load_dotenv()

USER = os.getenv('SENA_USUARIO')
PASSWORD = os.getenv('SENA_PASSWORD')
URL_LOGIN = 'https://caprendizaje.sena.edu.co/sgva/SGVA_Diseno/pag/login.aspx'

def find_real_urls():
    print("--- 🔍 Buscador de URLs Reales (Post-Login) ---")
    
    options = uc.ChromeOptions()
    driver = uc.Chrome(options=options)
    wait = WebDriverWait(driver, 30)
    
    try:
        print("1. Iniciando sesión...")
        driver.get(URL_LOGIN)
        wait.until(EC.element_to_be_clickable((By.ID, "aprendices"))).click()
        wait.until(EC.visibility_of_element_located((By.ID, "tbLoginUsuario"))).send_keys(USER)
        driver.find_element(By.ID, "__tbPasswordUsuario").send_keys(PASSWORD)
        driver.find_element(By.ID, "ini_session_aprendiz").click()
        
        print("⏳ Esperando 15 segundos para que la sesión se asiente...")
        time.sleep(15)
        
        print(f"📍 URL de aterrizaje actual: {driver.current_url}")
        
        # Limpiamos bloqueos visuales por si acaso
        driver.execute_script("""
            var elements = ['updProgress', 'updProgress1', 'IMGDIV', 'preloader'];
            elements.forEach(id => { var el = document.getElementById(id); if (el) el.remove(); });
            var overlays = document.querySelectorAll('.overLayBackground');
            overlays.forEach(ol => ol.remove());
            document.body.style.overflow = 'auto';
        """)

        print("\n--- 📋 MAPEO DE ENLACES ENCONTRADOS ---")
        links = driver.find_elements(By.TAG_NAME, "a")
        found_links = []
        
        for link in links:
            try:
                texto = link.text.strip()
                href = link.get_attribute("href")
                if texto or href:
                    found_links.append({"texto": texto, "href": href})
                    if "empresa" in texto.lower() or "buscar" in texto.lower():
                        print(f"🌟 ¡INTERESANTE! -> [{texto}] : {href}")
            except:
                continue

        if not found_links:
            print("⚠️ No se encontraron enlaces en esta página. Intentando buscar en IFRAMES...")
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            for i, frame in enumerate(iframes):
                print(f"Entrando al iframe {i}...")
                driver.switch_to.frame(frame)
                sub_links = driver.find_elements(By.TAG_NAME, "a")
                for sl in sub_links:
                    print(f"   - [{sl.text}] : {sl.get_attribute('href')}")
                driver.switch_to.default_content()

        # Guardamos todo para analizarlo
        with open('mapeo_urls.json', 'w', encoding='utf-8') as f:
            import json
            json.dump(found_links, f, ensure_ascii=False, indent=4)
        
        print("\n✅ Mapeo completado. Revisá la lista de arriba.")
        print("Si encontrás el link de 'Buscar Empresa', pasame la URL o el texto exacto.")
        
        # Mantenemos abierto para que el usuario pueda ver la página
        while True: time.sleep(1)

    except Exception as e:
        print(f"💥 Error: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    find_real_urls()
