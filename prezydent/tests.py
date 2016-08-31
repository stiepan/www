import unittest

from django.test import TestCase
from prezydent.models import MunicipalityType, Municipality, Candidate, CandidateResult
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from django.utils import timezone
from time import sleep


class TestAjax(TestCase):

    def setUp(self):
        muntm = MunicipalityType(name='miasto')
        muntm.save()
        munti = MunicipalityType(name='inne')
        munti.save()
        munin = Municipality(name='Miasto', type=muntm)
        munin.save()
        munact = Municipality(name='MiastoActive', type=muntm, dwellers=10, entitled=10, issued_cards=10, valid_votes=10,
                              votes=10)
        munact.save()
        c1 = Candidate(first_name='Kek', surname='Top', date_of_birth=timezone.now())
        c1.save()
        c2 = Candidate(first_name='Hue', surname='Hi', date_of_birth=timezone.now())
        c2.save()
        cr = CandidateResult(candidate=c1, municipality=munact, votes=6)
        cr.save()
        cr = CandidateResult(candidate=c2, municipality=munact, votes=4)
        cr.save()

    def test_results_omit_empty_types(self):
        m = MunicipalityType.objects.get(name='miasto')
        response = self.client.get('/results/detailed/type,' + str(m.id))
        response = response.json()

        assert response['status'] == 'OK'
        assert len(response['muni']) == 1


# Use it only when you have account testuser testpassword account
class SeleniumTest(unittest.TestCase):
    def setUp(self):
        self.browser = webdriver.Chrome
        self.base_url = 'http://127.0.0.1:8000'

    def test_login(self):
        brow = self.browser()
        baseurl = self.base_url
        adminurl = self.base_url + '/admin/'
        brow.get(adminurl)

        username = brow.find_element_by_id("id_username")
        password = brow.find_element_by_id("id_password")

        username.clear()
        username.send_keys('testuser')
        password.clear()
        password.send_keys('testpassword')
        brow.find_element_by_xpath('//input[@value="Zaloguj się" and @type="submit"]').click()
        brow.get(baseurl)

        sleep(1)
        logout = brow.find_element_by_id('logoutbut')
        assert logout
        logout.click()
        sleep(1)
        username = brow.find_element_by_id("id_username")
        password = brow.find_element_by_id("id_password")

        assert username
        assert password

        username.clear()
        username.send_keys('testuser')
        password.clear()
        password.send_keys('testpassword')
        brow.find_element_by_xpath('//input[@value=">" and @type="submit"]').click()
        sleep(1)
        assert brow.find_element_by_id('logoutbut')


    def test_editable(self):
        brow = self.browser()
        baseurl = self.base_url
        brow.get(baseurl)
        sleep(1)
        brow.find_element_by_xpath('//tr/td[@class="voiv_col_1"]').click()
        sleep(1)
        brow.find_element_by_xpath('//tr/td[@class="muni_col_1"]').click()
        sleep(1)
        good = False
        try:
            brow.find_element_by_id('save_but')
        except NoSuchElementException:
            good = True
        assert good