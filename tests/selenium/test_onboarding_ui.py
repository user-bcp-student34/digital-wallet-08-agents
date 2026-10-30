"""Prueba Selenium de la interfaz de onboarding (MVP básico funcional).

Rol: Testing (ver agents/testing.py). Automatiza el recorrido feliz de HU01
sobre el frontend Streamlit (src/frontend_mock.py), que a su vez llama a la
API local (src/main.py) y esta al mock real de KYC & Wallet.

Prerrequisitos (ver testing_report.md para el detalle):
    1. Backend corriendo:  uvicorn src.main:app --port 8000
    2. Frontend corriendo: streamlit run src/frontend_mock.py --server.port 8501
    3. Microsoft Edge instalado (Selenium Manager resuelve el driver automáticamente).

Ejecutar:
    pytest tests/selenium/test_onboarding_ui.py -v
    # o como script:
    python tests/selenium/test_onboarding_ui.py

Variables de entorno opcionales:
    FRONTEND_URL (por defecto http://localhost:8501)
"""
from __future__ import annotations

import os
import time
import uuid
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:8501")
SCREENSHOT_DIR = Path(__file__).parent / "screenshots"
SCREENSHOT_DIR.mkdir(exist_ok=True)


def _make_driver() -> webdriver.Edge:
    options = EdgeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1280,1024")
    return webdriver.Edge(options=options)


def _click_button(driver, wait: WebDriverWait, label: str) -> None:
    xpath = f'//div[@data-testid="stButton"]//button[normalize-space()="{label}"]'
    button = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
    button.click()


def _fill_input(driver, wait: WebDriverWait, aria_label: str, text: str) -> None:
    selector = f'input[aria-label="{aria_label}"]'
    field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
    field.clear()
    field.send_keys(text)
    field.send_keys(Keys.RETURN)
    time.sleep(0.3)


def test_onboarding_happy_path() -> None:
    """CA-01/CA-02/CA-03/CA-04: recorrido guiado completo hasta la landing ACTIVE_BASIC."""
    driver = _make_driver()
    wait = WebDriverWait(driver, 20)
    username = f"sel_{uuid.uuid4().hex[:8]}"

    try:
        driver.get(FRONTEND_URL)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="stTextInput"]')))
        driver.save_screenshot(str(SCREENSHOT_DIR / "01_datos_personales.png"))

        # Paso 1: datos personales
        _fill_input(driver, wait, "Nombres", "Selenium Prueba")
        _fill_input(driver, wait, "Apellido paterno", "Automatizado")
        _fill_input(driver, wait, "Apellido materno", "Delgado")
        _click_button(driver, wait, "Siguiente")

        # Paso 2: usuario
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[aria-label="Usuario"]')))
        _fill_input(driver, wait, "Usuario", username)
        wait.until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "disponible")]')))
        driver.save_screenshot(str(SCREENSHOT_DIR / "02_usuario_disponible.png"))
        _click_button(driver, wait, "Siguiente")

        # Paso 3: contraseña
        selector_pwd = 'input[aria-label="Contraseña"]'
        field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector_pwd)))
        field.send_keys("Selenium#2026Pwd")
        field.send_keys(Keys.RETURN)
        # Espera a que Streamlit rehaga el render con la robustez calculada
        # (y, por lo tanto, habilite "Siguiente") antes de capturar la evidencia.
        _click_button_xpath = '//div[@data-testid="stButton"]//button[normalize-space()="Siguiente"]'
        wait.until(EC.element_to_be_clickable((By.XPATH, _click_button_xpath)))
        driver.save_screenshot(str(SCREENSHOT_DIR / "03_password_strength.png"))
        _click_button(driver, wait, "Siguiente")

        # Paso 4: confirmación y envío
        wait.until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "Confirmación")]')))
        driver.save_screenshot(str(SCREENSHOT_DIR / "04_confirmacion.png"))
        _click_button(driver, wait, "Crear mi wallet")

        # Landing: bienvenida + saldo + aviso ACTIVE_BASIC
        wait.until(EC.presence_of_element_located((By.XPATH, '//*[contains(text(), "Bienvenido")]')))
        driver.save_screenshot(str(SCREENSHOT_DIR / "05_landing.png"))

        body_text = driver.find_element(By.TAG_NAME, "body").text
        assert "Bienvenido" in body_text, "No se mostró el saludo de bienvenida (CA-03)"
        assert "ACTIVE_BASIC" in body_text, "No se mostró el nivel ACTIVE_BASIC (CA-03)"
        assert "S/" in body_text, "No se mostró el saldo de la wallet (CA-03)"
    except Exception:
        driver.save_screenshot(str(SCREENSHOT_DIR / "_debug_failure.png"))
        (SCREENSHOT_DIR / "_debug_failure.html").write_text(driver.page_source, encoding="utf-8")
        raise
    finally:
        driver.quit()


if __name__ == "__main__":
    test_onboarding_happy_path()
    print("OK: recorrido feliz de onboarding validado en el navegador (ver screenshots/).")
