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
URL_DASHBOARD = 'https://caprendizaje.sena.edu.co/sgva/Aprendices/Index'

def session_hammer():
    print("--- 🔨 PASO 1: El Martillo de Sesión (Estabilizando Entrada) ---")
    
    options = uc.ChromeOptions()
    driver = uc.Chrome(options=options)
    wait = WebDriverWait(driver, 30)
    
    try:
        print("1. Cargando portal...")
        driver.get(URL_LOGIN)
        
        print("2. Seleccionando Aprendiz...")
        wait.until(EC.element_to_be_clickable((By.ID, "aprendices"))).click()
        time.sleep(2)
        
        print("3. Ingresando credenciales...")
        wait.until(EC.visibility_of_element_located((By.ID, "tbLoginUsuario"))).send_keys(USER)
        driver.find_element(By.ID, "__tbPasswordUsuario").send_keys(PASSWORD)
        
        print("4. Iniciando sesión...")
        driver.find_element(By.ID, "ini_session_aprendiz").click()
        
        # BUCLE DE ESTABILIZACIÓN: Vamos a intentar entrar 5 veces si sale el error
        for i in range(5):
            print(f"⏳ Intento de estabilización {i+1}/5...")
            time.sleep(10)
            
            source = driver.page_source.lower()
            url_actual = driver.current_url
            
            # Si vemos el error de permisos del SENA
            if "access to the path" in source or "server error" in source or "404" in url_actual:
                print("⚠️ El servidor del SENA sigue tirando error. Esperando un poco y reintentando salto...")
                time.sleep(5)
                # Intentamos forzar la URL del dashboard directamente
                driver.get(URL_DASHBOARD)
            else:
                # Verificamos si aparece el menú de Cerrar Sesión
                try:
                    if driver.find_elements(By.XPATH, "//*[contains(text(), 'Cerrar Sesión')] | //*[contains(text(), 'Buscar Empresa')]"):
                        print("\n✅ ¡LOGRADO! Superamos el error del servidor.")
                        print("Ya estamos adentro del Dashboard de forma estable.")
                        driver.save_screenshot("acceso_exitoso.png")
                        # Aquí paramos para que vos lo veas
                        while True: time.sleep(1)
                except:
                    print("... todavía no veo el Dashboard ...")
                    continue

        print("\n❌ El servidor del SENA está demasiado inestable hoy.")
        print("Si ves el Dashboard en la ventana abierta, avisame!")
        driver.save_screenshot("fallo_tras_reintentos.png")

    except Exception as e:
        print(f"💥 Error técnico: {str(e)}")
    finally:
        # Mantenemos abierto para inspección
        while True: time.sleep(1)

if __name__ == "__main__":
    session_hammer()
