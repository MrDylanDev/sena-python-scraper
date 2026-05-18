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

def run_diagnostic_jump():
    print("--- 📸 Diagnóstico de Bloqueo en Clic de Login ---")
    options = uc.ChromeOptions()
    driver = uc.Chrome(options=options)
    driver.maximize_window()
    wait = WebDriverWait(driver, 40)
    
    try:
        print("1. Abriendo portal...")
        driver.get(URL_LOGIN)
        
        print("2. Activando pestaña Aprendices...")
        btn_tab = wait.until(EC.element_to_be_clickable((By.ID, "aprendices")))
        driver.execute_script("arguments[0].click();", btn_tab)
        
        print("3. Poniendo credenciales...")
        wait.until(EC.visibility_of_element_located((By.ID, "tbLoginUsuario"))).send_keys(USER)
        driver.find_element(By.ID, "__tbPasswordUsuario").send_keys(PASSWORD)
        time.sleep(1)
        
        print("4. Clic en Iniciar Sesión...")
        driver.find_element(By.ID, "ini_session_aprendiz").click()
        
        # --- VERIFICACIÓN DE BLOQUEO ---
        print("⏳ Esperando 7 segundos de 'carga'...")
        time.sleep(7)
        
        print("📸 Tomando captura del bloqueo (verificando lo que ves)...")
        driver.save_screenshot("bloqueo_momento_login.png")
        
        # --- INTENTO DE SALTO FORZADO ---
        print("🚀 Intentando salto forzado al Dashboard (bypass de carga)...")
        driver.get("https://caprendizaje.sena.edu.co/sgva/Aprendices/Index")
        
        time.sleep(8)
        print(f"📍 URL tras el salto: {driver.current_url}")
        
        if "Index" in driver.current_url or "Solicitudes" in driver.current_url:
            print("✅ ¡EXITO! El salto funcionó. La sesión estaba creada.")
            driver.save_screenshot("salto_exitoso.png")
        else:
            print("⚠️ El salto falló. Intentando salto a Solicitudes directo...")
            driver.get("https://caprendizaje.sena.edu.co/sgva/Aprendices/Solicitudes/")
            time.sleep(8)
            if "Solicitudes" in driver.current_url:
                print("✅ ¡LOGRADO por la puerta de atrás!")
            else:
                print("❌ No hubo caso. El servidor no creó la sesión o está caído.")
                driver.save_screenshot("fallo_total_login.png")

    except Exception as e:
        print(f"💥 Error: {str(e)}")
    finally:
        print("\n--- Fin de diagnóstico ---")
        print("Revisá 'bloqueo_momento_login.png' para ver qué capturé.")
        # No cerramos para que veas el resultado
        while True: time.sleep(1)

if __name__ == "__main__":
    run_diagnostic_jump()
