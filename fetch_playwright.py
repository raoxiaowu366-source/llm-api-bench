from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://platform.sensenova.cn/docs")
    page.wait_for_load_state("networkidle")
    
    # We will try to extract all the text and then save it to a file
    # for further processing
    text = page.evaluate("document.body.innerText")
    
    with open("sensenova_docs_playwright.txt", "w", encoding="utf-8") as f:
        f.write(text)
        
    browser.close()
    
print("Playwright fetch complete.")
