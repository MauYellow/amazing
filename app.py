#11.01.25 14:52 - qui vorrò fare una prova per rendere il bot amazon disponibile per più canali
#creare un database online dove si possono modificare le scelte di ogni canale

#va tutto bene, però la lista delle offerte è comune ai canali, quindi il bot prende gli orari giusti ma invia le offerte sbagliate
#creata un field "offerte" in airtable per salvere le offerte lì? Oppure filtrare le offerte se l'id del canale è uguale?
#dai che ci sei, sta uscendo benissimo, non sarà facile ma vedrai che ne varrà la pena.

#per portarla a github copiare il .py e rinominarlo app.py e inserirlo dentro la cartella Bot Amazon

from paapi5_python_sdk.api.default_api import DefaultApi
from paapi5_python_sdk.models.partner_type import PartnerType
from paapi5_python_sdk.models.search_items_request import SearchItemsRequest
from paapi5_python_sdk.models.search_items_resource import SearchItemsResource
from paapi5_python_sdk.rest import ApiException
import time, schedule
from telegram import Bot
import requests
import os
from dotenv import load_dotenv
from flask import Flask
import threading
from datetime import datetime
import json
import re

load_dotenv("env.txt")

app = Flask(__name__)

@app.route('/')
def hello():
    return "Ciao, il tuo servizio funziona!"

#Airtable
airtable_token = "patroCNF4sUF6jdbk.21bf50b0df1095dca0cf6aa5255016a833dc157baeba13d6700f10d4f96e68ad"
airtable_headers = {
    "Authorization": f"Bearer {airtable_token}",
    #"Content-type": "application/json"
}
airtable_url = "https://api.airtable.com/v0/appk7bV1OTtjoJFd7/Amazon%20Bot%20Python"
airtable_channels = []

# Telegram Variable
botkey = os.getenv("botkey")
chat = os.getenv("chat")
message = "Messaggio"
bot = Bot(botkey)
headers = {"content-type": "application/json"}
url_bot = f"https://api.telegram.org/bot{botkey}/sendMessage"
owner_chat_id = os.getenv("owner_chat_id")
scheduled_time = ["08:00", "08:30", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00"]
bot_offers = []
tasks = 0
chosen_categories = ["Apparel", "Handmade", "GardenAndOutdoor"] #tutte le opzioni qui https://webservices.amazon.com/paapi5/documentation/locale-reference/italy.html
chosen_min_percentage = 5
data = {
    "chat_id": chat,
    "text": message,
    "parse_mode": "Markdown",
    "disable_web_page_preview": True,
}
lista_canali = []
lista_canali_prova = {}



def photo_message(offerta): ## da sostituire bot_offers con offerta
  if len(bot_offers) > 0: # forse da eliminare?
    print(offerta)
    print(f"Offerta inviata a: {offerta['id_canale']}")
    data = {
      "chat_id": offerta['id_canale'],
      "caption": f"""
🔥 *Nuova offerta*: {offerta['Title']}

🖊️ *Descrizione*: {offerta['Description']}

🔖 *Sconto*: {offerta['Discount Percentage']}%
💰 *Nuovo Prezzo*: {offerta['New Price']} invece di {offerta['Old price']}€

🛒 *Accedi all'offerta*: {offerta['Url']}
""",
    "photo": offerta['Img'],
    "parse_mode": "Markdown",
    "disable_web_page_preview": True,
    "reply_markup": {
      "inline_keyboard": [
        [
            {"text": offerta['button_text'], "url": offerta['button_url']}
        ],
        [
            {"text": "Richiedi un bot Telegram", "url": "https://t.me/programmazione_bot_telegram"}
        ]
    ]
}
    }

    response_bot = requests.post(f"https://api.telegram.org/bot{botkey}/sendPhoto", headers=headers, json=data)
    if response_bot.status_code == 200:
      print(f"Foto delle {time.strftime('%H:%M:%S', time.localtime())} inviata con successo, {len(bot_offers) - 1} offerte rimanenti")
      bot_offers.pop(0)
    else:
      print(f"Errore: {response_bot.status_code}")

  else:
    data = {
      "chat_id": owner_chat_id,
      "text": "❌ Pubblicazione non avvenuta: Non ci sono più offerte disponibili, hai forse parametri troppo restrittivi? La prossima lista si aggiornerà domani mattina",
}
    response_bot = requests.post(f"https://api.telegram.org/bot{botkey}/sendMessage", headers=headers, json=data)
    if response_bot.status_code == 200:
      print("No More Offers Available sent")
    else:
      print(f"Errore: {response_bot.status_code}")

def group_message(): # Non utilizzato, solo di prova
  data["text"] = f"""
  {bot_offers[0]["Img"]}
  Nuova offerta: {bot_offers[0]["Title"]}
  Sconto: {bot_offers[0]["Discount Percentage"]}
  Accedi all'offerta: {bot_offers[0]["Url"]}"""
  response_bot = requests.post(url_bot, headers=headers, json=data)
  if response_bot.status_code == 200:
    print("Messaggio inviato con successo!")
    print(response_bot.json())
    bot_offers.pop(0)

  else:
    print(f"Errore nell'invio del messaggio. Status code: {response_bot.status_code}")
    print(response_bot.text)
  print(response_bot)

def prova_messaggio(): # Non utilizzato solo di prova
  data["text"] = "Prova messaggio"
  response_bot = requests.post(url_bot, headers=headers, json=data)
  if response_bot.status_code == 200:
    print("Messaggio inviato con successo!")
    print(response_bot.json())
    bot_offers.pop(0)
  else:
    print(f"Errore nell'invio del messaggio. Status code: {response_bot.status_code}")
    print(response_bot.text)



def search_items(page, category, id_canale, partnerTag, minimosconto, button_text, button_url): #16.01 qui bisogna appendere l'offerta all'interno del dictionary (lista_canali) con id il canaleid
    access_key = os.getenv("access_key")
    secret_key = os.getenv("secret_key")
    partner_tag = "maulink-21"
    host = "webservices.amazon.it"
    region = "eu-west-1"
    MinSavingPercent = minimosconto
    #keywords = "Harry Potter"
    search_index = category 
    item_count = 10
    default_api = DefaultApi(
        access_key=access_key, secret_key=secret_key, host=host, region=region
    )

    search_items_resource = [
        SearchItemsResource.ITEMINFO_TITLE,
        SearchItemsResource.OFFERS_LISTINGS_PRICE,
        SearchItemsResource.BROWSENODEINFO_BROWSENODES,
        SearchItemsResource.IMAGES_PRIMARY_LARGE,
        SearchItemsResource.CUSTOMERREVIEWS_COUNT, #NON FUNZIONA
        SearchItemsResource.CUSTOMERREVIEWS_STARRATING, #NON FUNZIONA
        SearchItemsResource.OFFERS_LISTINGS_PROMOTIONS, #NON FUNZIONA
        SearchItemsResource.OFFERS_LISTINGS_SAVINGBASIS #prezzo prima dello sconto
    ]
    """ Forming request """
    try:
        search_items_request = SearchItemsRequest(
            partner_tag=partner_tag,
            partner_type=PartnerType.ASSOCIATES,
            #keywords=keywords,
            min_saving_percent=MinSavingPercent,
            search_index=search_index,
            item_count=item_count,
            resources=search_items_resource,
            item_page=page,
            min_reviews_rating=4,
        )
    except ValueError as exception:
        print("Error in forming SearchItemsRequest: ", exception)
        return
    try:
        """ Sending request """
        response = default_api.search_items(search_items_request)
        print("API called Successfully")
        print(f"Parnter Tag found: {partnerTag}")
        """ Parse response """  
        if response.search_result is not None:
            item_0 = response.search_result.items[0]
            print(f"Lunghezza lista: {len(response.search_result.items)}")
            offers = response.search_result.items
            for offer in offers:
                new_url = re.sub(r'(tag=)[^&]*', rf'\1{partnerTag}', offer.detail_page_url)
                print(f"Offerta con nuovo partner tag: {new_url}") # re.sub(r'(tag=)[^&]*', rf'\1{partnerTag}', offer.detail_page_url) 
                if offer.offers.listings[0].price.savings is not None:
                  if offer.offers.listings[0].price.savings.percentage > minimosconto:
                    if not {"Title": offer.browse_node_info.browse_nodes[0].display_name, "Description": offer.item_info.title.display_value, "Old price": offer.offers.listings[0].saving_basis.amount, "New Price": offer.offers.listings[0].price.display_amount, "Discount Percentage": offer.offers.listings[0].price.savings.percentage, "Url": new_url, "Img": offer.images.primary.large.url} in bot_offers: # vecchio url offer.detail_page_url
                      bot_offers.append({"id_canale": id_canale, "Title": offer.browse_node_info.browse_nodes[0].display_name, "Description": offer.item_info.title.display_value, "Old price": offer.offers.listings[0].saving_basis.amount, "New Price": offer.offers.listings[0].price.display_amount, "Discount Percentage": offer.offers.listings[0].price.savings.percentage, "Url": new_url, "Img": offer.images.primary.large.url})
                      #print(f"Lista canali: {lista_canali}")
                      for x in lista_canali: #occhio che l'ho definita come [] appena sopra questa funzione
                        title = offer.browse_node_info.browse_nodes[0].display_name
                        if id_canale in x:
                           x[f'{id_canale}'].append({"id_canale": id_canale, "Title": title.replace("_", " "), "Description": offer.item_info.title.display_value, "Old price": offer.offers.listings[0].saving_basis.amount, "New Price": offer.offers.listings[0].price.display_amount, "Discount Percentage": offer.offers.listings[0].price.savings.percentage, "Url": new_url, "Img": offer.images.primary.large.url, "button_text": button_text, "button_url": button_url})
                           break
                    else:
                      print("Doppione eliminato correttamente.")
            if item_0 is not None:
                if item_0.asin is not None:
                    print("ASIN: ", item_0.asin)
                if item_0.detail_page_url is not None:
                    print("DetailPageURL: ", item_0.detail_page_url)
                if (
                    item_0.item_info is not None
                    and item_0.item_info.title is not None
                    and item_0.item_info.title.display_value is not None
                ):
                    print("Title: ", item_0.item_info.title.display_value)
                if (
                    item_0.offers is not None
                    and item_0.offers.listings is not None
                    and item_0.offers.listings[0].price is not None
                    and item_0.offers.listings[0].price.display_amount is not None
                ):
                    print("Buying Price: ", item_0.offers.listings[0].price.display_amount)
                    print("Sconto Percentuale:", item_0.offers.listings[0].price.savings.percentage, "%")
        if response.errors is not None:
          print("\nPrinting Errors:\nPrinting First Error Object from list of Errors")
          print("Error code", response.errors[0].code)
          print("Error message", response.errors[0].message)
    except ApiException as exception:
        print("Error calling PA-API 5.0!")
        print("Status code:", exception.status)
        print("Errors :", exception.body)
        print("Request ID:", exception.headers["x-amzn-RequestId"])
    except TypeError as exception:
        print("TypeError :", exception)
    except ValueError as exception:
        print("ValueError :", exception)
    except Exception as exception:
        print("Exception :", exception)

def empty_offers():
   global tasks
   tasks = tasks + 1
   global bot_offers
   bot_offers = []
   print("Offers list is now restarted")

def main():
  print("Starting main function..")
  for channel in airtable_channels:
    global tasks
    tasks = tasks + 1
    if len(channel['categorie']) == 1:
      print("categoria trovata: 1")
      for page in range(1,5): #da tornare a 1,6
          print("**********")
          print(page, channel['categorie'][0], channel['id_canale'])
          print("**********")
          search_items(page, channel['categorie'][0], channel['id_canale'], channel['partnerTag'], channel['minimosconto'], channel['button_text'], channel['button_url'])
          time.sleep(2)
    else:
      print(f"categorie trovate: {len(channel['categorie'])}")
      for category in channel['categorie']:
          for page in range(1,5): #da tornare a 1,6
            search_items(page, category, channel['id_canale'], channel['partnerTag'], channel['minimosconto'], channel['button_text'], channel['button_url'])
            time.sleep(3)
    bot_offers.sort(key=lambda x: x["Discount Percentage"], reverse=True)
    new_offer = {"fields": {"offerte": f"{bot_offers}"}}
    response_patch = requests.patch(airtable_url + "/" + channel['row_id'], headers=airtable_headers, json=new_offer)
    print("*** Response Patch:")
    print(response_patch.status_code)
    print(response_patch)
    print(bot_offers)

def read_airtable():
  response = requests.get(airtable_url, headers=airtable_headers)    
  airtable_data = response.json()
  print(len(airtable_data['records']))
  print("------")
  print(airtable_data)
  print("------")
  print(response.status_code)
  airtable_channels = []
  for row in airtable_data['records']:
    airtable_channels.append(
      {
        "row_id": row['id'],
        "id_canale": row['fields']['id_canale'],
        "categorie": row['fields']['categorie'].split(", "),
        "orario": row['fields']['orario'].split(", "),
        "minimosconto": row['fields']['minimosconto'],
        "offerte": [], #qui si azzera la lista, anche se non serve?!
        "partnerTag": row['fields']['partnerTag'],
        "button_text": row['fields']['button_text'],
        "button_url": row['fields']['button_url']
        #"owner_chat_id": row['fields']['owner_chat_id'] - questo è ancora da confermare
        }
        )
    print(row['fields']['id_canale'])
  print("***")
  print(airtable_channels)
  print("***")
  lista_canali = []
  for id_canali in airtable_channels:
    lista_canali.append({f"{id_canali['id_canale']}": []})
    lista_canali_prova[f'{id_canali['id_canale']}'] = []
  print(f"Risultato: {lista_canali}")
  print(f"Risultato_prova: {lista_canali_prova}")

def fill_offers():
   print("---")
   print(f"Lista canali: {lista_canali}")
   print(len(lista_canali))
   id = 0
   for channel in airtable_channels:
      offerte = lista_canali[id][f'{channel['id_canale']}']
      channel['offerte'] = offerte
      print(f"Nuovo channel: {channel}")
      id = id + 1


def scheduling():
  print("--")
  print(airtable_channels)
  for channel in airtable_channels:
    print(f"Debug channel: {channel}")
    channel_id = channel['id_canale']
    time.sleep(2)
    offer_id = 0
    for post_time in channel['orario']:
      time.sleep(2)
      if offer_id < len(channel['offerte']):
        print(f"*Offerta: {channel['offerte'][offer_id]}, Canale: {channel_id}; Canale2: {channel['offerte'][offer_id]['id_canale']}, Alle ore: {post_time}")
        print(f"Debug post_time: {post_time}")
        print(f"Offerta da inviare: {channel['offerte'][offer_id]}")
        print(f"Nel canale: {channel_id}")
        offerta = channel['offerte'][offer_id]
        schedule.every().day.at(f"{post_time}").do(lambda off=offerta: photo_message(off))
        offer_id = offer_id + 1
      else:
        break


print(f"Ora server: {datetime.now()}")

#ricorda che l'orario del server è un'ora indietro

def prova(offerta): ## da sostituire bot_offers con offerta
  if len(bot_offers) >= 0:
    print(offerta)
    print(f"Offerta inviata a: {offerta['id_canale']}")
    data = {
      "chat_id": offerta['id_canale'],
      "caption": f"""
🔥 *Nuova offerta*: {offerta['Title']}

🖊️ *Descrizione*: {offerta['Description']}

🔖 *Sconto*: {offerta['Discount Percentage']}%
💰 *Nuovo Prezzo*: {offerta['New Price']} invece di {offerta['Old price']}€

🛒 *Accedi all'offerta*: {offerta['Url']}
""",
    "photo": offerta['Img'],
    "parse_mode": "Markdown",
    "disable_web_page_preview": True,
}
    response_bot = requests.post(f"https://api.telegram.org/bot{botkey}/sendPhoto", headers=headers, json=data)
    if response_bot.status_code == 200:
      print(f"Foto delle {time.strftime('%H:%M:%S', time.localtime())} inviata con successo, {len(bot_offers) - 1} offerte rimanenti")
      bot_offers.pop(0)
    else:
      print(f"Errore: {response_bot.status_code}")

  else:
    data = {
      "chat_id": owner_chat_id,
      "text": "❌ Pubblicazione non avvenuta: Non ci sono più offerte disponibili, hai forse parametri troppo restrittivi? La prossima lista si aggiornerà domani mattina",
}
    response_bot = requests.post(f"https://api.telegram.org/bot{botkey}/sendMessage", headers=headers, json=data)
    if response_bot.status_code == 200:
      print("No More Offers Available sent")
    else:
      print(f"Errore: {response_bot.status_code}")

#prova()
#read_airtable()
#empty_offers()
#main()
#fill_offers()
#scheduling()

schedule.every().day.at("22:00:00").do(read_airtable)
schedule.every().day.at("22:05:00").do(empty_offers)
schedule.every().day.at("22:06:00").do(main)
schedule.every().day.at("22:10:00").do(fill_offers)
schedule.every().day.at("22:15:00").do(scheduling)

# 08.00 read airtable: quanti canali sono (se nuovi) e categorie nuove
# 08.10 empty offers
# 08.20 main (filla le offerte)
# 08.30 scheduling


def schedule_runner():
    global tasks
    while True:
        if len(bot_offers) > 0:
            time.sleep(3)
            print(f"Prossima offerta: {bot_offers[0]['Title']}, Prezzo: {bot_offers[0]['New Price']}, Sconto: {bot_offers[0]['Discount Percentage']} %")
            schedule.run_pending()
        else:
            schedule.run_pending()
            time.sleep(3)
            print(f"Tasks: {tasks}")
            if tasks > 0:
                schedule.run_pending()
                tasks -= 1
        time.sleep(1)  # Previene l'uso eccessivo della CPU

schedule_thread = threading.Thread(target=schedule_runner)
schedule_thread.daemon = True  # Assicura che il thread termini con il programma principale
schedule_thread.start()

# Programma principale (simulazione)
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
    print("Bot avviato. Attività pianificate in esecuzione...")
    try:
        while True:
            time.sleep(1)  # Mantieni il programma attivo
    except KeyboardInterrupt:
        print("Chiusura del bot.")




#DA MODIFICARE

#credo che airtable_channels vada azzerato ogni giorno per aggiornamenti (altrimenti appende su una lista già esistente)
#anche lista_canali
#range pagina tornare da 2 a 6
#minimo prezzo?
#ho creato button_text e button_url vanno modificati in base al canale, nella variabile offerta?
#ad ogni annuncio, bottone con "vuoi bot telegram?"
#pubblica ancora offerte con minisconto inferiore a quanto deve - fatto ma bisogna controllare
# quando accoppia gli orari alle offerte, può mandare un messaggio all'owner che dice "non ci sono offerte per questo orario" (perché la lista è troppo corta e troppe restrizioni)
# <- lo dice al momento della creazione delle liste, non al momento del minuto in cui deve inviarlo

#cambiare owner chat id ed il modo in cui gli viene comunicato (ora è legato a bot_offers) - da verificare, come faccio?
#call back data funzione telegram per vedere quanti click si fanno al bottone
#ogni offerta pubblicata va in una lista published_lista con len massima di 20 items, e se l'offerta che sta per essere pubblicata è stata già pubblicata, la scarta
# I doppioni non li elimina perché hanno ASIN o Img diverso? Dovrei confrontere i Title per eliminarli 
#Fare in modo che se si parla in privato con il bot possa dire se vuole un suo canale amazon
#eliminare offerte che costano meno di 20€

#OK
# scheduling, se i minimosconto sono troppo restrittivi, da meno offerte, e se da meno offerte da errore perché non trova l'index di offer_id
#Quando ci sta la lista piena time.sleep(3) print "Lista Piena, prossimo annuncio alle.."
#il bot sorta la lista discendente basandosi su percentage discount
#4. Gamification
#Sistema di punti: Premia gli utenti attivi (ad esempio, che cliccano sui link o condividono offerte) con punti da convertire in vantaggi, come accesso a offerte esclusive.
#Classifiche: Mostra una classifica degli utenti più attivi o di quelli che hanno trovato le migliori offerte.
#Quiz e premi: Organizza quiz o piccoli giochi con premi legati a offerte.
#Vinci buono Amazon


categorie_disponibili =[
    "Apparel",  # Abbigliamento
    "Appliances",  # Grandi elettrodomestici
    "Automotive",  # Auto e Moto
    "Baby",  # Prima infanzia
    "Beauty",  # Bellezza
    "Books",  # Libri
    "Computers",  # Informatica
    "DigitalMusic",  # Musica Digitale
    "Electronics",  # Elettronica
    "EverythingElse",  # Altro
    "Fashion",  # Moda
    "ForeignBooks",  # Libri in altre lingue
    "GardenAndOutdoor",  # Giardino e giardinaggio
    "GiftCards",  # Buoni Regalo
    "GroceryAndGourmetFood",  # Alimentari e cura della casa
    "Handmade",  # Handmade
    "HealthPersonalCare",  # Salute e cura della persona
    "HomeAndKitchen",  # Casa e cucina
    "Industrial",  # Industria e Scienza
    "Jewelry",  # Gioielli
    "KindleStore",  # Kindle Store
    "Lighting",  # Illuminazione
    "Luggage",  # Valigeria
    "MobileApps",  # App e Giochi
    "MoviesAndTV",  # Film e TV
    "Music",  # CD e Vinili
    "MusicalInstruments",  # Strumenti musicali e DJ
    "OfficeProducts",  # Cancelleria e prodotti per ufficio
    "PetSupplies",  # Prodotti per animali domestici
    "Shoes",  # Scarpe e borse
    "Software",  # Software
    "SportsAndOutdoors",  # Sport e tempo libero
    "ToolsAndHomeImprovement",  # Fai da te
    "ToysAndGames",  # Giochi e giocattoli
    "VideoGames",  # Videogiochi
    "Watches",  # Orologi
]