#!/usr/bin/env python

from selenium import selenium
import unittest, time, re

class SitBidPlay(unittest.TestCase):
    def setUp(self):
        self.verificationErrors = []
        self.seleniumN = selenium('localhost', 4444, '*chrome', 'http://localhost:8080/')
        self.seleniumN.start()
        self.seleniumE = selenium('localhost', 4444, '*chrome', 'http://localhost:8080/')
        self.seleniumE.start()
        self.seleniumS = selenium('localhost', 4444, '*chrome', 'http://localhost:8080/')
        self.seleniumS.start()
        self.seleniumW = selenium('localhost', 4444, '*chrome', 'http://localhost:8080/')
        self.seleniumW.start()
    
    def test_sit_bid_play(self):
        selN = self.seleniumN
        selE = self.seleniumE
        selS = self.seleniumS
        selW = self.seleniumW

        selN.open('table.html?newtest01')
        selN.type('id=email', 'TestN')
        selN.click('id=submit-login')
        time.sleep(2)
        baseurl = selN.get_location()[:-1]
        print baseurl
        selE.open(baseurl + 'E')
        selE.type('id=email', 'TestE')
        selE.click('id=submit-login')
        time.sleep(1)

        selS.open(baseurl + 'S')
        selS.type('id=email', 'TestS')
        selS.click('id=submit-login')
        time.sleep(1)

        selW.open(baseurl + 'W')
        selW.type('id=email', 'TestW')
        selW.click('id=submit-login')
        time.sleep(1)

        selN.click("id=bid_1D")
        time.sleep(1)
        selE.click("id=bid_pass")
        time.sleep(1)
        selS.click("id=bid_pass")
        time.sleep(1)
        selW.click("id=bid_pass")
        return
        for i in range(60):
            try:
                if "pass" == sel.get_text("xpath=//table[@id='bidding_area']//tr[2]/td[2]"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        for i in range(60):
            try:
                if "pass" == sel.get_text("xpath=//table[@id='bidding_area']//tr[2]/td[3]"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        for i in range(60):
            try:
                if "pass" == sel.get_text("xpath=//table[@id='bidding_area']//tr[2]/td[4]"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        self.failIf(sel.is_visible("id=bidbox"))
        self.failUnless(sel.is_visible("id=lead_area"))
        for i in range(60):
            try:
                if sel.is_element_present("xpath=//div[@id='E_lead']/span[@id='card_14']"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.click("id=card_13")
        sel.click("id=card_13")
        for i in range(60):
            try:
                if sel.is_element_present("xpath=//div[@id='W_lead']/span[@id='card_20']"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.click("id=card_21")
        sel.click("id=card_21")
        for i in range(60):
            try:
                if "1" == sel.get_text("xpath=//span[@id='NS_tricks']"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.click("id=card_15")
        sel.click("id=card_15")
        for i in range(60):
            try:
                if sel.is_element_present("xpath=//div[@id='E_lead']/span[@id='card_25']"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.click("id=card_18")
        sel.click("id=card_18")
        for i in range(60):
            try:
                if sel.is_element_present("xpath=//div[@id='W_lead']/span[@id='card_17']"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        for i in range(60):
            try:
                if sel.is_element_present("xpath=//div[@id='E_lead']/span[@id='card_16']"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.click("id=card_23")
        sel.click("id=card_23")
        for i in range(60):
            try:
                if sel.is_element_present("xpath=//div[@id='W_lead']/span[@id='card_42']"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.click("id=card_19")
        sel.click("id=card_19")
        sel.click("id=card_3")
        sel.click("id=card_3")
        for i in range(60):
            try:
                if sel.is_element_present("xpath=//div[@id='W_lead']/span[@id='card_0']"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.click("id=card_7")
        sel.click("id=card_7")
        for i in range(60):
            try:
                if sel.is_element_present("xpath=//div[@id='E_lead']/span[@id='card_11']"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        for i in range(60):
            try:
                if sel.is_element_present("xpath=//div[@id='E_lead']/span[@id='card_41']"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.click("id=card_39")
        sel.click("id=card_39")
        for i in range(60):
            try:
                if sel.is_element_present("xpath=//div[@id='W_lead']/span[@id='card_48']"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.click("id=card_51")
        sel.click("id=card_51")
        sel.click("id=card_26")
        sel.click("id=card_26")
        for i in range(60):
            try:
                if sel.is_element_present("xpath=//div[@id='E_lead']/span[@id='card_27']"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.click("id=card_38")
        sel.click("id=card_38")
        for i in range(60):
            try:
                if sel.is_element_present("xpath=//div[@id='W_lead']/span[@id='card_31']"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.click("id=card_33")
        sel.click("id=card_33")
        for i in range(60):
            try:
                if sel.is_element_present("xpath=//div[@id='W_lead']/span[@id='card_36']"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.click("id=card_37")
        sel.click("id=card_37")
        for i in range(60):
            try:
                if sel.is_element_present("xpath=//div[@id='E_lead']/span[@id='card_28']"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.click("id=card_35")
        sel.click("id=card_35")
        for i in range(60):
            try:
                if sel.is_element_present("xpath=//div[@id='E_lead']/span[@id='card_29']"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.click("id=card_40")
        sel.click("id=card_40")
        for i in range(60):
            try:
                if sel.is_element_present("xpath=//div[@id='W_lead']/span[@id='card_5']"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.click("id=card_12")
        sel.click("id=card_12")
        for i in range(60):
            try:
                if sel.is_element_present("xpath=//div[@id='E_lead']/span[@id='card_1']"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.click("id=card_8")
        sel.click("id=card_8")
        for i in range(60):
            try:
                if sel.is_element_present("xpath=//div[@id='W_lead']/span[@id='card_6']"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.click("id=card_4")
        sel.click("id=card_4")
        for i in range(60):
            try:
                if sel.is_element_present("xpath=//div[@id='E_lead']/span[@id='card_2']"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.click("id=card_10")
        sel.click("id=card_10")
        for i in range(60):
            try:
                if sel.is_element_present("xpath=//div[@id='W_lead']/span[@id='card_9']"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.click("id=card_45")
        sel.click("id=card_45")
        for i in range(60):
            try:
                if sel.is_element_present("xpath=//div[@id='W_lead']/span[@id='card_49']"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.click("id=card_44")
        sel.click("id=card_44")
        for i in range(60):
            try:
                if sel.is_element_present("xpath=//div[@id='E_lead']/span[@id='card_30']"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        for i in range(60):
            try:
                if sel.is_element_present("xpath=//div[@id='W_lead']/span[@id='card_50']"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.click("id=card_22")
        sel.click("id=card_22")
        for i in range(60):
            try:
                if sel.is_element_present("xpath=//div[@id='E_lead']/span[@id='card_32']"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.click("id=card_46")
        sel.click("id=card_46")
        sel.click("id=card_24")
        sel.click("id=card_24")
        for i in range(60):
            try:
                if sel.is_element_present("xpath=//div[@id='E_lead']/span[@id='card_34']"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        sel.click("id=card_47")
        sel.click("id=card_47")
        for i in range(60):
            try:
                if sel.is_element_present("xpath=//div[@id='W_lead']/span[@id='card_43']"): break
            except: pass
            time.sleep(1)
        else: self.fail("time out")
        # sel.()
    
    def tearDown(self):
        self.seleniumN.stop()
        self.seleniumE.stop()
        self.seleniumS.stop()
        self.seleniumW.stop()
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    unittest.main()
