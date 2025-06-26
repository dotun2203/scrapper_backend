import os, csv, time, re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoAlertPresentException, NoSuchElementException,
    TimeoutException, StaleElementReferenceException,
    ElementClickInterceptedException,
)
from webdriver_manager.chrome import ChromeDriverManager

def scrape_nysc(year: str) -> str:
    URL = "https://portal.nysc.org.ng/nysc1/CheckInstitutionCoursesPCMs.aspx"
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    filename = f"nysc_data_{year}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    filepath = os.path.join(output_dir, filename)

    ROW_DELAY = 0.25
    SHOW_SIZE = "100"
    row_selector = ("table[id$='GdvPCMCourses'] tbody tr, "
                    "table[id$='gvCourses'] tbody tr")

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--blink-settings=imagesEnabled=false")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 10)

    def pairs(sid):
        return [(o.get_attribute("value"), o.text.strip())
                for o in Select(driver.find_element(By.ID, sid)).options
                if o.get_attribute("value") not in ("","0")]

    def pick(sel_id, *, value=None, text=None):
        for _ in range(3):
            try:
                s = Select(driver.find_element(By.ID, sel_id))
                s.select_by_value(value) if value else s.select_by_visible_text(text)
                time.sleep(ROW_DELAY); return True
            except (StaleElementReferenceException, NoSuchElementException):
                time.sleep(0.3)
        return False

    def alert_or_none():
        try:
            a = driver.switch_to.alert
            t = a.text.strip(); a.accept(); return t
        except NoAlertPresentException:
            return None

    def set_page_length():
        for name in ("GdvPCMCourses_length", "gvCourses_length"):
            try:
                Select(driver.find_element(By.NAME, name)).select_by_visible_text(SHOW_SIZE)
                time.sleep(ROW_DELAY)
                return
            except NoSuchElementException:
                continue

    # Write header
    with open(filepath, 'w', encoding='utf-8', newline='') as csv_f:
        wr = csv.writer(csv_f)
        wr.writerow(["Batch","Programme","Institution","Course",
                     "S/No","Surname","Other Names","Gender","Course Name","Status"])
        rows_written = 0
        try:
            driver.get(URL)
            wait.until(EC.presence_of_element_located((By.ID,"ctl00_ContentPlaceHolder1_cboBatch")))
            batches = [p for p in pairs("ctl00_ContentPlaceHolder1_cboBatch") if year in p[1]]
            for b_val, b_txt in batches:
                pick("ctl00_ContentPlaceHolder1_cboBatch", value=b_val)
                for p_val, p_txt in pairs("ctl00_ContentPlaceHolder1_cbo1stMostInstitutionType"):
                    pick("ctl00_ContentPlaceHolder1_cbo1stMostInstitutionType", value=p_val)
                    for i_val, i_txt in pairs("ctl00_ContentPlaceHolder1_cboFirstInstitution"):
                        pick("ctl00_ContentPlaceHolder1_cboFirstInstitution", value=i_val)
                        t0 = time.time()
                        while not (courses:=pairs("ctl00_ContentPlaceHolder1_cboCourses")) and time.time()-t0<8:
                            time.sleep(0.3)
                        for _, c_txt in courses:
                            if c_txt.lower().startswith("select"): continue
                            pick("ctl00_ContentPlaceHolder1_cboCourses", text=c_txt)
                            try:
                                btn = driver.find_element(By.ID,"ctl00_ContentPlaceHolder1_btnExtract")
                                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                                time.sleep(0.1)
                                btn.click()
                            except ElementClickInterceptedException:
                                driver.execute_script("arguments[0].click();", btn)
                            time.sleep(ROW_DELAY/2)
                            time.sleep(0.5)
                            if alert_or_none():
                                driver.back(); time.sleep(ROW_DELAY); continue
                            set_page_length()
                            try:
                                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, row_selector)))
                                for tr in driver.find_elements(By.CSS_SELECTOR, row_selector):
                                    td=[t.text.strip() for t in tr.find_elements(By.TAG_NAME,"td")]
                                    if len(td)!=6: continue
                                    row=[b_txt,p_txt,i_txt,c_txt,*td]
                                    wr.writerow(row)
                                    rows_written+=1
                                csv_f.flush(); os.fsync(csv_f.fileno())
                                driver.back(); time.sleep(ROW_DELAY)
                                time.sleep(ROW_DELAY)
                            except TimeoutException:
                                driver.back(); time.sleep(ROW_DELAY)
                                continue
        finally:
            driver.quit()
    return filename