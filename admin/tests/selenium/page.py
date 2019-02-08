from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.action_chains import ActionChains


class BasePage(object):
    """Base class to initialize the base page that will be called from all pages"""

    def __init__(self, driver):
        self.driver = driver
        driver.set_window_size(1024, 1024)

    def find_element(self, by, value, timeout=None):
        if timeout:
            return WebDriverWait(self.driver, timeout).until(
                expected_conditions.presence_of_element_located((by, value)))
        else:
            return self.driver.find_element(by, value)

    def select_language(self, locale):
        self.find_element(By.XPATH, '//li[@id="language-dropdown"]').click()
        self.find_element(
            By.XPATH,
            '//a[contains(@href,"language={}")]'.format(locale)
        ).click()

    def wait_jquery_to_be_active(self):
        WebDriverWait(self.driver, 10).until(
            lambda driver: driver.execute_script(
                'return (window.jQuery != undefined && jQuery.active == 0)'))

    def dbl_click(self, el):
        action_chains = ActionChains(self.driver)
        # following event implies use of chrome selenium web driver instead of gecko (Firefox)
        action_chains.move_to_element(el).double_click().perform()

    def click_and_confirm(self, el):
        el.click()
        self.driver.switch_to_alert().accept()
        self.driver.switch_to_default_content()


class IndexPage(BasePage):

    def select_page_size(self, size, timeout=None):
        page_list = self.find_element(By.XPATH, '//*[@class="page-list"]', timeout)
        page_list.find_element(By.XPATH, './/button[@data-toggle="dropdown"]').click()
        page_list.find_element(By.XPATH, './/a[text()="{}"]'.format(size)).click()

    def check_pagination_info(self, expected, timeout):
        WebDriverWait(self.driver, timeout).until(
            expected_conditions.text_to_be_present_in_element(
                (By.XPATH, '//span[@class="pagination-info"]'),
                expected))

    def find_item_action(self, id_, action):
        td = self.find_element(By.XPATH, '//tr[@data-uniqueid="{}"]/td[@class="actions"]'.format(id_))
        td.find_element(By.XPATH, './/button[@data-target="item-{}-actions"]'.format(id_)).click()
        return td.find_element(By.XPATH, './/a[contains(@class, "{}")]'.format(action))

    def click_delete(self, id_):
        self.click_and_confirm(self.find_item_action(id_, 'delete'))


class LayertreePage(BasePage):

    def expand(self):
        button = self.find_element(By.ID, 'layertree-expand', 10)
        WebDriverWait(self.driver, 10).until(
            expected_conditions.visibility_of(button))
        button.click()

    def find_item(self, path, timeout=None):
        return self.find_element(
            By.CSS_SELECTOR,
            'li.jstree-node[id="{}"]'.format(path), timeout)

    def find_item_action(self, path, action, timeout=None):
        dropdown = self.find_element(
            By.CSS_SELECTOR,
            '.jstree-grid-column.actions '
            '.jstree-grid-cell[data-jstreegrid="' + path + '"] '
            '.dropdown',
            timeout=10)
        button = dropdown.find_element(By.XPATH, './/button[@data-toggle="dropdown"]')
        WebDriverWait(self.driver, 10).until(
            expected_conditions.visibility_of(button))
        button.click()
        return dropdown.find_element(By.CSS_SELECTOR, 'a.{}'.format(action))
