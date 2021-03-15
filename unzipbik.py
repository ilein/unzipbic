import requests
import zipfile
import io
import os
import glob
import xml.etree.ElementTree as ET


class BankBic:
    def __init__(self, bic, full_name, account, city, adr, datein, postalcode):
        self.bic = bic
        self.full_name = full_name
        self.short_name = self._getShortName(full_name)
        self.account = account
        self.city = city
        self.adr = adr
        self.datein = datein
        self.postalcode = postalcode

    def __repr__(self):
        return self.bic + ' ' + \
               self.short_name + ' ' + \
               self.full_name + ' ' + \
               self.account + ' ' + \
               self.city + ' ' + \
               self.adr + ' ' + \
               self.datein + ' ' + \
               self.postalcode

    def getStrDataFormated(self):
        if self.datein == '':
            strd = ''
        else:
            strd = 'to_date(\'%s\', \'yyyy-mm-dd\')' % self.datein
        str = 'tp_ldr_bank_bik(\'%s\', \'%s\', \'%s\', \'%s\', ' \
              '%s, \'%s\', \'%s\', \'%s\')' % \
              (self.full_name, self.full_name, self.bic, self.account,
               strd, self.postalcode, self.city, self.adr)
        return str

    def _getShortName(self, str):
        ind_s = str.find('"')
        ind_e = str.find('"', ind_s + 1)
        if ind_s > -1:
            return str[ind_s + 1:ind_e]
        else:
            return str.split(' ')[0]


def clearPath(path):
    files = glob.glob(path+'/*')
    for f in files:
        os.remove(f)


def unzipFile(path):
    r = requests.get('http://cbr.ru/s/newbik')
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall(path)


def getLastFileName(path):
    list_of_files = glob.glob(path+'/*.xml')
    latest_file = max(list_of_files, key=os.path.getctime)
    return latest_file

def parseDIREnrtyToBic(dirEntry):
    bic = dirEntry.attrib['BIC']

    pinf = dirEntry.find('x:ParticipantInfo', ns)
    full_name = pinf.attrib['NameP']
    city = pinf.attrib.get('Nnp', '')
    adr = pinf.attrib.get('Adr', '')
    datein = pinf.attrib.get('DateIn', '')
    postalcode = pinf.attrib.get('Ind', '')

    account = ''
    for acc in dirEntry.findall('x:Accounts', ns):
        if acc.attrib['RegulationAccountType'] == 'CRSA':
            account = acc.attrib['Account']
            break

    b = BankBic(bic, full_name, account, city, adr, datein, postalcode)
    return b


bikpath = 'bik'
clearPath(bikpath)
unzipFile(bikpath)

myFile = getLastFileName(bikpath)

tree = ET.parse(myFile)
root = tree.getroot()

ns = {'x': 'urn:cbr-ru:ed:v2.0'}

bicList = []

for member in root.findall('x:BICDirectoryEntry', ns):
    b = parseDIREnrtyToBic(member)
    bicList.append(b)

try:
    os.remove('biktype.txt')
except OSError:
    pass

f = open('biktype.txt', 'w')
print('tp_ldr_bank_bik_tbl(', file=f)
for i in range(len(bicList)):
    if i < len(bicList)-1:
        print(bicList[i].getStrDataFormated()+', ', sep='\n', file=f)
    else:
        print(bicList[i].getStrDataFormated()+')', sep='\n', file=f)
f.close()
