import os
import time
import re
import json
from dotenv import load_dotenv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

load_dotenv()

USER = os.getenv('SENA_USUARIO')
PASSWORD = os.getenv('SENA_PASSWORD')
URL_LOGIN = 'https://caprendizaje.sena.edu.co/sgva/SGVA_Diseno/pag/login.aspx'
URL_DASHBOARD = 'https://caprendizaje.sena.edu.co/sgva/Aprendices/Index'

def run_scraper_final():
    print("--- 🚀 INICIANDO EXTRACCIÓN TOTAL (Antioquia) ---")
    
    options = uc.ChromeOptions()
    driver = uc.Chrome(options=options)
    wait = WebDriverWait(driver, 40)
    
    def limpiar_basura_visual():
        # Borramos cualquier overlay o spinner que el SENA deje pegado
        driver.execute_script("""
            var elements = ['updProgress', 'updProgress1', 'IMGDIV', 'preloader', 'modal-backdrop'];
            elements.forEach(id => { 
                var el = document.getElementById(id); if (el) el.remove(); 
                var cl = document.querySelector('.' + id); if (cl) cl.remove();
            });
            var overlays = document.querySelectorAll('.overLayBackground');
            overlays.forEach(ol => ol.remove());
            document.body.style.overflow = 'auto';
        """)

    try:
        # --- PASO 1: LOGIN (Lógica exitosa) ---
        print("1. Iniciando sesión...")
        driver.get(URL_LOGIN)
        wait.until(EC.element_to_be_clickable((By.ID, "aprendices"))).click()
        time.sleep(2)
        wait.until(EC.visibility_of_element_located((By.ID, "tbLoginUsuario"))).send_keys(USER)
        driver.find_element(By.ID, "__tbPasswordUsuario").send_keys(PASSWORD)
        driver.find_element(By.ID, "ini_session_aprendiz").click()
        
        # Estabilización
        time.sleep(12)
        if "Index" not in driver.current_url:
            print("⚠️ URL incorrecta, forzando Dashboard...")
            driver.get(URL_DASHBOARD)
            time.sleep(8)
            
        limpiar_basura_visual()

        # --- PASO 2: IR A BUSCAR EMPRESA ---
        print("2. Navegando a 'Buscar Empresa'...")
        try:
            # Buscamos el link en el menú
            btn_buscar = wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Buscar Empresa')]")))
            driver.execute_script("arguments[0].click();", btn_buscar)
        except:
            print("⚠️ Link de menú no encontrado, saltando directo a la URL de consulta...")
            driver.get("https://caprendizaje.sena.edu.co/sgva/SGVA_Diseno/pag/ConsultarEmpresa.aspx")
            
        time.sleep(8)
        limpiar_basura_visual()

        # --- PASO 3: FILTRAR ANTIOQUIA ---
        print("3. Filtrando por departamento: ANTIOQUIA...")
        # Localizamos el selector de departamento
        dept_el = wait.until(EC.presence_of_element_located((By.XPATH, "//select[contains(@id, 'ddlDepartamento')]")))
        Select(dept_el).select_by_visible_text("ANTIOQUIA")
        time.sleep(2)
        
        print("Ejecutando búsqueda...")
        # Clic en el botón de consulta
        driver.execute_script("document.querySelector('input[value*=\"Consultar\"], [id*=\"btnConsultar\"], input[value*=\"Buscar\"]').click();")
        
        print("⏳ Cargando resultados (8 seg)...")
        time.sleep(10)
        limpiar_basura_visual()

        # --- PASO 4: EXTRACCIÓN MASIVA ---
        results = []
        # Buscamos botones "Ver-aplicar"
        botones = driver.find_elements(By.XPATH, "//input[@value='Ver-aplicar'] | //a[contains(text(), 'Ver-aplicar')]")
        total = len(botones)
        print(f"\n📢 ¡LOGRADO! Encontré {total} empresas para procesar.")

        for i in range(total):
            try:
                # Re-localizar botones (por si el DOM cambia)
                btns_actuales = driver.find_elements(By.XPATH, "//input[@value='Ver-aplicar'] | //a[contains(text(), 'Ver-aplicar')]")
                btn = btns_actuales[i]
                
                # Scroll y Clic forzado
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", btn)
                
                print(f"   [{i+1}/{total}] Abriendo detalles...")
                time.sleep(5) # Espera del modal
                
                # Extraer texto total de la página para buscar el mail
                source = driver.page_source
                emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', source)
                email_final = emails[0] if emails else "No encontrado"
                
                # Intentamos sacar el nombre de la empresa
                try:
                    nombre = driver.execute_script("return document.querySelector('[id*=\"lblNombreEmpresa\"], h4, h3').innerText")
                except:
                    nombre = f"Empresa {i+1}"
                
                print(f"      🏢 {nombre.strip()} -> 📧 {email_final}")
                results.append({"empresa": nombre.strip(), "correo": email_final})
                
                # Cerrar modal (Escape)
                driver.find_element(By.TAG_NAME, "body").send_keys("\ue00c")
                time.sleep(2)
                
            except Exception as e:
                print(f"      ⚠️ Error en esta tarjeta, continuando...")
                driver.find_element(By.TAG_NAME, "body").send_keys("\ue00c")

        # --- PASO 5: GUARDAR ---
        with open('patrocinios_antioquia.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
            
        print(f"\n✨ FINALIZADO CON ÉXITO ✨")
        print(f"Se extrajeron {len(results)} correos y se guardaron en 'patrocinios_antioquia.json'")

    except Exception as e:
        print(f"💥 Fallo crítico: {str(e)}")
        driver.save_screenshot("fallo_extraccion.png")
    finally:
        print("Cerrando navegador...")
        driver.quit()

if __name__ == "__main__":
    run_scraper_final()
