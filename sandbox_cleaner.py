import pywikibot


site = pywikibot.Site('pl', 'wikiquote')
sandboxPage = pywikibot.Page(site, 'Wikicytaty:Brudnopis')
sandboxTemplate = '{{Prosimy - NIE ZMIENIAJ, NIE KASUJ, NIE PRZENOŚ tej linijki - pisz niżej}}'
sandboxPage.text = sandboxTemplate

sandboxPage.save('Bot czyści brudnopis')