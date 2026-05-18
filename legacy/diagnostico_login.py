import os
import time
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

def diagnosticar_bloqueo_login():
    print("--- 📸 Diagnóstico de Carga Infinita en Login ---")
    options = uc.ChromeOptions()
    driver = uc.Chrome(options=options)
    driver.maximize_window()
    wait = WebDriverWait(driver, 60)
    
    try:
        print("1. Cargando portal...")
        driver.get(URL_LOGIN)
        
        print("2. Seleccionando Aprendices...")
        btn_tab = wait.until(EC.element_to_be_clickable((By.ID, "aprendices")))
        driver.execute_script("arguments[0].click();", btn_tab)
        
        print("3. Ingresando datos...")
        wait.until(EC.visibility_of_element_located((By.ID, "ini_session_aprendiz")))
        driver.find_element(By.ID, "tbLoginUsuario").send_keys(USER)
        driver.find_element(By.ID, "__tbPasswordUsuario").send_keys(PASSWORD)
        
        print("4. Clic en Iniciar Sesión...")
        driver.find_element(By.ID, "ini_session_aprendiz").click()
        
        print("⏳ Esperando 20 segundos para capturar el estado de carga...")
        time.sleep(20)
        
        print("📸 Tomando captura del bloqueo...")
        driver.save_screenshot("fallo_login_infinito.png")
        
        print("📄 Guardando código fuente del error...")
        with open("source_bloqueo_login.html", "w", encoding='utf-8') as f:
            f.write(driver.page_source)
            
        url_actual = driver.current_url
        print(f"📍 URL en el momento del bloqueo: {url_actual}")
        
        # Analizar si hay mensajes de error visibles
        try:
            error_text = driver.find_element(By.ID, "Label21").text
            if error_text:
                print(f"❌ Error detectado en pantalla: {error_text}")
        except:
            pass

        print("\n--- Diagnóstico finalizado ---")
        print("Revisá 'fallo_login_infinito.png' y 'source_bloqueo_login.html'")

    except Exception as e:
        print(f"💥 Error durante el diagnóstico: {str(e)}")
    finally:
        print("Navegador abierto para inspección manual.")

if __name__ == "__main__":
    diagnosticar_bloqueo_login()
