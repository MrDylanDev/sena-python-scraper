import os
import time
from dotenv import load_dotenv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

load_dotenv()

USER = os.getenv('SENA_USUARIO')
PASSWORD = os.getenv('SENA_PASSWORD')

def capture_login_moment():
    print("--- 📸 Captura de Momento Login ---")
    driver = uc.Chrome()
    try:
        driver.get('https://caprendizaje.sena.edu.co/sgva/SGVA_Diseno/pag/login.aspx')
        time.sleep(3)
        driver.find_element(By.ID, "aprendices").click()
        time.sleep(2)
        driver.find_element(By.ID, "tbLoginUsuario").send_keys(USER)
        driver.find_element(By.ID, "__tbPasswordUsuario").send_keys(PASSWORD)
        time.sleep(1)
        
        print("Haciendo clic en Iniciar Sesión...")
        # Clic por JS para evitar bloqueos del driver
        driver.execute_script("document.getElementById('ini_session_aprendiz').click();")
        
        # Esperamos 10 segundos para ver el estado de carga
        print("Esperando 10 segundos...")
        time.sleep(10)
        
        driver.save_screenshot("login_moment.png")
        print("📸 Captura 'login_moment.png' guardada.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    capture_login_moment()
