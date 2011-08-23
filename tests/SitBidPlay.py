#!/usr/bin/env python

from selenium import selenium
import unittest, time, re

class SitBidPlay(unittest.TestCase):
    def setUp(self):
        self.verificationErrors = []
        self.seleniumN = selenium('localhost', 4444, '*firefox', 'http://localhost:8080/')
        self.seleniumN.start()
        self.seleniumE = selenium('localhost', 4444, '*firefox', 'http://localhost:8080/')
        self.seleniumE.start()
        self.seleniumS = selenium('localhost', 4444, '*firefox', 'http://localhost:8080/')
        self.seleniumS.start()
        self.seleniumW = selenium('localhost', 4444, '*firefox', 'http://localhost:8080/')
        self.seleniumW.start()
    
    def test_sit_bid_play(self):
        selN = self.seleniumN
        selE = self.seleniumE
        selS = self.seleniumS
        selW = self.seleniumW

        selN.open('table.html?newtest01')
        selN.type('id=email', 'TestN')
        selN.click('id=submit-login')
        time.sleep(4)
        baseurl = selN.get_location()[:-1]
        selE.open(baseurl + 'E')
        selE.type('id=email', 'TestE')
        selE.click('id=submit-login')
        time.sleep(4)

        selS.open(baseurl + 'S')
        selS.type('id=email', 'TestS')
        selS.click('id=submit-login')
        time.sleep(4)

        selW.open(baseurl + 'W')
        selW.type('id=email', 'TestW')
        selW.click('id=submit-login')
        time.sleep(4)

        selN.click("id=bid_1D")
        time.sleep(2)
        selE.click("id=bid_pass")
        time.sleep(2)
        selS.click("id=bid_pass")
        time.sleep(2)
        selW.click("id=bid_pass")
#        self.failIf(sel.is_visible("id=bidbox"))
#        self.failUnless(sel.is_visible("id=lead_area"))

        time.sleep(2)
        selE.double_click('id=card_14')
        time.sleep(2)
        selN.double_click('id=card_13')
        time.sleep(2)
        selW.double_click('id=card_20')
        time.sleep(2)
        selN.double_click('id=card_21')

# wait till sel.get_text('id=NS_tricks') == '1'
        time.sleep(1)
        selN.double_click('id=card_15')
        time.sleep(1)
        selE.double_click('id=card_25')
        time.sleep(1)
        selN.double_click('id=card_18')
        time.sleep(1)
        selW.double_click('id=card_17')

        time.sleep(1)
        selE.double_click('id=card_16')
        time.sleep(1)
        selN.double_click('id=card_23')
        time.sleep(1)
        selW.double_click('id=card_42')
        time.sleep(1)
        selN.double_click('id=card_19')

        time.sleep(1)
        selN.double_click('id=card_3')
        time.sleep(1)
        selW.double_click('id=card_0')
        time.sleep(1)
        selN.double_click('id=card_7')
        time.sleep(1)
        selE.double_click('id=card_11')

        time.sleep(1)
        selE.double_click('id=card_41')
        time.sleep(1)
        selN.double_click('id=card_39')
        time.sleep(1)
        selW.double_click('id=card_48')
        time.sleep(1)
        selN.double_click('id=card_51')

        time.sleep(1)
        selN.double_click('id=card_26')
        time.sleep(1)
        selE.double_click('id=card_27')
        time.sleep(1)
        selN.double_click('id=card_38')
        time.sleep(1)
        selW.double_click('id=card_31')

        time.sleep(1)
        selN.double_click('id=card_33')
        time.sleep(1)
        selW.double_click('id=card_36')
        time.sleep(1)
        selN.double_click('id=card_37')
        time.sleep(1)
        selE.double_click('id=card_28')

        time.sleep(1)
        selN.double_click('id=card_35')
        time.sleep(1)
        selE.double_click('id=card_29')
        time.sleep(1)
        selN.double_click('id=card_40')
        time.sleep(1)
        selW.double_click('id=card_5')

        time.sleep(1)
        selN.double_click('id=card_12')
        time.sleep(1)
        selE.double_click('id=card_1')
        time.sleep(1)
        selN.double_click('id=card_8')
        time.sleep(1)
        selW.double_click('id=card_6')

        time.sleep(1)
        selN.double_click('id=card_4')
        time.sleep(1)
        selE.double_click('id=card_2')
        time.sleep(1)
        selN.double_click('id=card_10')
        time.sleep(1)
        selW.double_click('id=card_9')

        time.sleep(1)
        selN.double_click('id=card_45')
        time.sleep(1)
        selW.double_click('id=card_49')
        time.sleep(1)
        selN.double_click('id=card_44')
        time.sleep(1)
        selE.double_click('id=card_30')

        time.sleep(1)
        selW.double_click('id=card_50')
        time.sleep(1)
        selN.double_click('id=card_22')
        time.sleep(1)
        selE.double_click('id=card_32')
        time.sleep(1)
        selN.double_click('id=card_46')

        time.sleep(1)
        selN.double_click('id=card_24')
        time.sleep(1)
        selE.double_click('id=card_34')
        time.sleep(1)
        selN.double_click('id=card_47')
        time.sleep(1)
        selW.double_click('id=card_43')

    
    def tearDown(self):
        self.seleniumN.click('xpath=//span[@id=\'user_header\']/a[2]')
        self.seleniumE.click('xpath=//span[@id=\'user_header\']/a[2]')
        self.seleniumS.click('xpath=//span[@id=\'user_header\']/a[2]')
        self.seleniumW.click('xpath=//span[@id=\'user_header\']/a[2]')
        self.seleniumN.stop()
        self.seleniumE.stop()
        self.seleniumS.stop()
        self.seleniumW.stop()
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    unittest.main()
