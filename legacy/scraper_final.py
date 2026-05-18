import os
import time
import re
import json
import random
from dotenv import load_dotenv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

load_dotenv()

USER = os.getenv('SENA_USUARIO')
PASSWORD = os.getenv('SENA_PASSWORD')
URL_LOGIN = 'https://caprendizaje.sena.edu.co/sgva/SGVA_Diseno/pag/login.aspx'

def limpiar_basura_eterna(driver):
    driver.execute_script("""
        setInterval(function() {
            var loader = document.querySelector('.modalCargando, #updProgress, .overLayBackground');
            if (loader) loader.remove();
            var form = document.getElementById('div_formulario_busqueda');
            if (form) { form.style.display = 'block'; form.style.visibility = 'visible'; }
            document.body.style.overflow = 'auto';
        }, 500);
    """)

def run_scraper_ultimate():
    print("--- ⚡ Scraper v32: Control Total por Inyección ---")
    options = uc.ChromeOptions()
    driver = uc.Chrome(options=options)
    driver.maximize_window()
    wait = WebDriverWait(driver, 60)
    
    final_data = []
    
    try:
        # 1. LOGIN ATÓMICO
        driver.get(URL_LOGIN)
        time.sleep(5)
        print("1. Inyectando sesión...")
        driver.execute_script(f"""
            document.getElementById('aprendices').click();
            setTimeout(function() {{
                document.getElementById('tbLoginUsuario').value = '{USER}';
                document.getElementById('__tbPasswordUsuario').value = '{PASSWORD}';
                document.getElementById('ini_session_aprendiz').click();
            }}, 1500);
        """)
        
        # 2. ESPERA Y SALTO
        time.sleep(12)
        limpiar_basura_eterna(driver)
        driver.get("https://caprendizaje.sena.edu.co/sgva/Aprendices/Solicitudes/")
        time.sleep(10)

        # 3. FILTRADO POR INYECCIÓN (NO FALLA)
        print("2. Filtrando Antioquia (Vía Código)...")
        driver.execute_script("""
            var sel = document.getElementById('sel_departamento');
            if(sel) {
                sel.value = '5';
                var evt = document.createEvent('HTMLEvents');
                evt.initEvent('change', true, true);
                sel.dispatchEvent(evt);
            }
            setTimeout(function() {
                var btn = document.getElementById('btn_buscar_solicitud');
                if(btn) btn.click();
            }, 1000);
        """)
        
        # 4. EXTRACCIÓN TOTAL
        pagina = 1
        xpath_btns = "//button[contains(@class, 'aprendizBotonInterno')] | //*[contains(text(), 'Ver-aplicar')]"
        
        while True:
            print(f"\n📄 PROCESANDO PÁGINA {pagina}")
            time.sleep(12)
            limpiar_basura_eterna(driver)
            
            btns = driver.find_elements(By.XPATH, xpath_btns)
            btns_visibles = [b for b in btns if b.is_displayed()]
            print(f"   -> {len(btns_visibles)} empresas encontradas.")

            if not btns_visibles: break

            for i in range(len(btns_visibles)):
                try:
                    actual_btns = driver.find_elements(By.XPATH, xpath_btns)
                    btn = [b for b in actual_btns if b.is_displayed()][i]
                    driver.execute_script("arguments[0].click();", btn)
                    
                    email = ""
                    for _ in range(6):
                        time.sleep(3)
                        email = driver.execute_script("return document.getElementById('lbl_modal_solicitud_email').innerText").strip()
                        if "@" in email: break
                    
                    nombre = driver.execute_script("return document.getElementById('lbl_modal_solicitud_especialidad').innerText").strip()
                    print(f"      🏢 {nombre[:30]}... -> 📧 {email if email else 'Sin correo'}")
                    
                    if email:
                        final_data.append({"oferta": nombre, "correo": email})
                        with open('patrocinios_lista_completa_v32.json', 'w', encoding='utf-8') as f:
                            json.dump(final_data, f, ensure_ascii=False, indent=4)
                    
                    driver.execute_script("document.getElementById('btn_modal_solicitud_cerrar').click();")
                    time.sleep(random.uniform(2, 4))
                except:
                    driver.find_element(By.TAG_NAME, "body").send_keys("\ue00c")

            # BUSCADOR DE PAGINACIÓN
            try:
                btn_sig = driver.find_elements(By.XPATH, f"//a[text()='{pagina + 1}'] | //button[contains(text(), 'Siguiente')] | //*[@id='btn_pagina_siguiente']")
                encontrado = False
                for b in btn_sig:
                    if b.is_displayed():
                        print(f"➡️ Saltando a página {pagina + 1}...")
                        driver.execute_script("arguments[0].click();", b)
                        pagina += 1
                        encontrado = True
                        break
                if not encontrado: break
            except: break

        print(f"\n✨ ¡HECHO! {len(final_data)} correos extraídos.")

    except Exception as e:
        print(f"💥 Error: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_scraper_ultimate()
