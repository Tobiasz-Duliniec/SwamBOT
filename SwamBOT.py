from pywikibot import xmlreader
import datetime
import os
import pywikibot
import re
import time


class Swambot:
    def __init__(self):
        self.maxQuoteLength = 1000
        self.tooLongQuotePage = 'Użytkownik:SwamBOT/Zbyt długie cytaty'
        self.deadLinksTemplate = 'link-do-sprawdzenia'
        self.lastCheckedPageFile = 'lastpageid.txt'
        self.pathToDatabaseDump = 'plwikiquote-20251001-pages-articles.xml.bz2'
        self.site = pywikibot.Site('pl', 'wikiquote')
        self.pagesToCheckPerRun = 1000
    
    def format_date(self, date: str) -> str:
        '''
        Replaces English month names to Polish month names in date string
        '''
        replacements = {'January': 'stycznia',
                        'February': 'lutego',
                        'March': 'marca',
                        'April': 'kwietnia',
                        'May': 'maja',
                        'June': 'czerwca',
                        'July': 'lipca',
                        'August': 'sierpnia',
                        'September': 'września',
                        'October': 'października',
                        'November': 'listopada',
                        'December': 'grudnia'}
        for month in replacements:
            if month in date:
                return date.replace(month, replacements[month])
        return date
    
    def checkForDeadLinks(self, page: pywikibot.xmlreader.XmlEntry) -> None:
        '''
        Checks if the links are dead and informs about it
        '''
        deadLinks = self.getDeadLinksList(page.text)
        if(len(deadLinks) > 0):
            discussionPage = pywikibot.Page(self.site, 'Dyskusja:' + page.title)
            linkTemplates = ''
            for link in deadLinks:
                if(('{{' + self.deadLinksTemplate + '|link=' + link[0]) not in discussionPage.text):
                    linkTemplates += '{{' + self.deadLinksTemplate + '|link=' + link[0] + '|problem=' + link[1] + '|data=' + link[2] + '}}\n'
            discussionPage.text = linkTemplates + discussionPage.text
            discussionPage.save('Bot zgłasza problemy z linkami')
            
    
    def getDeadLinksList(self, pageText: str) -> list:
        '''
        Returns a list of dead links
        '''
        deadLinks = []
        seenLinks = set()
        for link in re.findall('https?:\/\/(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?:[\/?#][^\s]*)?', pageText):
            if link in seenLinks: continue
            seenLinks.add(link)
            date = self.format_date(datetime.datetime.strftime(datetime.datetime.utcnow(), '%d %B %Y, %H:%M (UTC)'))
            try:
                #fake_useragent module is required for faked useragents
                r = pywikibot.comms.http.fetch(link, use_fake_user_agent = True)
                if(r.status_code >= 300 or r.status_code < 200):
                    deadLinks.append( (link, str(r.status_code), date) )
            except Exception as e:
                if('Caused by SSLError(SSLCertVerificationError' in str(e)):
                    deadLinks.append( (link, f'podczas łączenia ze stroną wystąpił wyjątek: [https://doc.wikimedia.org/pywikibot/master/api_ref/exceptions.html {e.__class__.__name__} (najprawdopodobniej wystąpił błąd z certyfikatem SSL)]', date) )
                else:
                    deadLinks.append( (link, f'podczas łączenia ze stroną wystąpił wyjątek: [https://doc.wikimedia.org/pywikibot/master/api_ref/exceptions.html {e.__class__.__name__}]', date) )
            time.sleep(10)
        return deadLinks

    def informAboutTooLongQuote(self, page: pywikibot.xmlreader.XmlEntry, quoteList: list) -> None:
        '''
        Informs about too long quotes on a page's talk page
        '''
        pageToInform = pywikibot.Page(site, self.tooLongQuotePage)
        addedLinks = 0
        for quote in quoteList:
            textToAdd = f"\n* Na stronie [[{page.title}]] znaleziono zbyt długi cytat o długości {len(quote)} znaków: ''{quote}''"
            if textToAdd in pageToInform.text: continue
            textToAdd += ' ~~~~'
            addedLinks += 1
            pageToInform.text += textToAdd
        pageToInform.save('Bot zgłasza zbyt długi cytat' if addedLinks == 1 else 'Bot zgłasza zbyt długie cytaty')

    def getQuoteLength(self, quote: str) -> int:
        '''
        Returns the length of a quote
        '''
        if quote.startswith('* '):
            quote = quote[2:]
        quote = quote.replace('<br>', ' ').replace('<br />', ' ').replace('<br/>', ' ').replace('</br>', ' ').replace('</ br>', ' ').replace('(...) ', '').replace('(…) ', '').replace('[...] ', '').replace('[…] ', '')
        return len(quote)

    def checkForTooLongQuotes(self, page: pywikibot.xmlreader.XmlEntry) -> None:
        '''
        Check if a quote is too long
        '''
        quoteList = []
        for line in page.text.splitlines():
            if line.startswith('* ') and self.getQuoteLength(line) > self.maxQuoteLength:
                quoteList.append(line[2:])
        if len(quoteList) > 0:
            self.informAboutTooLongQuote(page, quoteList) 

    def saveLastCheckedPage(self, pageId: str) -> None:
        '''
        Saves the title of a last page that was checked by the bot
        '''
        with open(self.lastCheckedPageFile, 'wt', encoding='UTF-8') as file:
            file.write(pageId)

    def readLastCheckedPage(self) -> int:
        '''
        Read the id of a last page that was checked by the bot
        '''
        if os.path.isfile(self.lastCheckedPageFile):
            with open(self.lastCheckedPageFile, 'rt', encoding='UTF-8') as file:
                return int(next(file))
        return 1

    def mainWorkLoop(self):
        '''
        Main loop of the bot
        '''
        checked_pages = 0
        lastCheckedId = self.readLastCheckedPage()
        dump = xmlreader.XmlDump(self.pathToDatabaseDump, revisions='latest')
        for elem in dump.parse():
            if(int(elem.id) <= lastCheckedId): continue
            if(elem.ns == '0'):
                checked_pages += 1
                print(elem.title)
                #self.saveLastCheckedPage(elem.id)
                #self.checkForDeadLinks(elem)
                #self.checkForTooLongQuotes(elem)
                if(checked_pages >= self.pagesToCheckPerRun):
                    return
        self.saveLastCheckedPage('1')

bot = Swambot()
bot.mainWorkLoop()


