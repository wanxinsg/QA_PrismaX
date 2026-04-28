from playwright.sync_api import Page,expect



def test_login_pw(page:Page)->None:
    page.goto("https://www.google.com")
    page.screenshot(path="google.png")
    expect(page).to_have_title("Google")
