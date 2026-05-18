import os
import time
import re
import json
from dotenv import load_dotenv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

load_dotenv()

USER = os.getenv('SENA_USUARIO')
PASSWORD = os.getenv('SENA_PASSWORD')
URL_LOGIN = 'https://caprendizaje.sena.edu.co/sgva/SGVA_Diseno/pag/login.aspx'

def run_human_scraper():
    print("--- 👤 Scraper v9: Emulación Humana Total ---")
    
    options = uc.ChromeOptions()
    driver = uc.Chrome(options=options)
    wait = WebDriverWait(driver, 60) # Espera generosa
    actions = ActionChains(driver)
    
    try:
        print("1. Abriendo el portal...")
        driver.get(URL_LOGIN)
        time.sleep(5)
        
        print("2. Seleccionando Aprendices (Clic Físico)...")
        btn_aprendices = wait.until(EC.element_to_be_clickable((By.ID, "aprendices")))
        actions.move_to_element(btn_aprendices).click().perform()
        time.sleep(3)
        
        print("3. Ingresando credenciales...")
        user_field = wait.until(EC.visibility_of_element_located((By.ID, "tbLoginUsuario")))
        
        # Tipeo pausado
        for char in USER:
            user_field.send_keys(char)
            time.sleep(0.1)
        
        time.sleep(1)
        pass_field = driver.find_element(By.ID, "__tbPasswordUsuario")
        for char in PASSWORD:
            pass_field.send_keys(char)
            time.sleep(0.1)
        
        time.sleep(2)
        
        print("4. Iniciando sesión (Emulación de Mouse)...")
        login_btn = driver.find_element(By.ID, "ini_session_aprendiz")
        
        # Movemos el mouse al botón, esperamos y clickeamos "físicamente"
        actions.move_to_element(login_btn).pause(1).click_and_hold().pause(0.5).release().perform()
        
        print("⏳ Esperando que el portal procese el inicio de sesión naturalmente...")
        # NO forzamos navegación. Esperamos a que la URL cambie sola.
        try:
            # Esperamos a que la URL ya no sea la de login
            wait.until(lambda d: "login.aspx" not in d.current_url.lower())
            print(f"✅ ¡La página cambió! Nueva ubicación: {driver.current_url}")
        except:
            print("⚠️ El portal no cambió de página tras 60 segundos.")
            print("Verifica si apareció algún mensaje de error en rojo en la ventana.")
            driver.save_screenshot("captura_estatico.png")
            return

        # Si llegamos acá, es porque logramos entrar
        print("\n--- 🔍 Iniciando Búsqueda de Empresas ---")
        # Buscamos el botón de Buscar Empresa
        btn_buscar = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Buscar Empresa')]")))
        actions.move_to_element(btn_buscar).click().perform()
        
        time.sleep(5)
        
        print("Filtrando Antioquia...")
        from selenium.webdriver.support.ui import Select
        dept_el = wait.until(EC.presence_of_element_located((By.XPATH, "//select[contains(@id, 'ddlDepartamento')]")))
        Select(dept_el).select_by_visible_text("ANTIOQUIA")
        time.sleep(2)
        
        print("Ejecutando búsqueda...")
        # Clic físico en buscar
        btn_consultar = driver.find_element(By.XPATH, "//input[contains(@id, 'btnConsultar')] | //input[contains(@value, 'Consultar')]")
        actions.move_to_element(btn_consultar).click().perform()
        
        print("⏳ Cargando resultados...")
        time.sleep(10)
        
        # Extracción
        results = []
        botones = driver.find_elements(By.XPATH, "//input[@value='Ver-aplicar'] | //a[contains(text(), 'Ver-aplicar')]")
        print(f"📢 Se encontraron {len(botones)} empresas.")

        for i in range(len(botones)):
            try:
                btns = driver.find_elements(By.XPATH, "//input[@value='Ver-aplicar'] | //a[contains(text(), 'Ver-aplicar')]")
                btn = btns[i]
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                time.sleep(2)
                
                # Clic físico en Ver-aplicar
                actions.move_to_element(btn).click().perform()
                
                print(f"   [{i+1}/{len(botones)}] Extrayendo...")
                time.sleep(5)
                
                source = driver.page_source
                emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', source)
                email = emails[0] if emails else "No encontrado"
                
                results.append({"empresa": f"Empresa {i+1}", "correo": email})
                print(f"      📧 {email}")
                
                # Cerrar modal
                driver.find_element(By.TAG_NAME, "body").send_keys("\ue00c")
                time.sleep(2)
            except:
                driver.find_element(By.TAG_NAME, "body").send_keys("\ue00c")

        with open('resultados_sena.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
        print("\n✅ PROCESO FINALIZADO.")

    except Exception as e:
        print(f"💥 Error: {str(e)}")
    finally:
        print("Manteniendo navegador abierto para revisión.")
        # Mantenemos abierto para que veas qué pasó
        while True: time.sleep(1)

if __name__ == "__main__":
    run_human_scraper()
