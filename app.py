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
load_dotenv("env.txt")

# Telegram Variable
botkey = os.getenv("botkey")
chat = os.getenv("chat")
message = "Messaggio"
bot = Bot(botkey)
headers = {"content-type": "application/json"}
url_bot = f"https://api.telegram.org/bot{botkey}/sendMessage"
owner_chat_id = os.getenv("owner_chat_id")
scheduled_time = ["10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00", "20:00", "21:00", "22:00"]
bot_offers = []
tasks = 0
chosen_categories = ["SportsAndOutdoors", "Books"]
data = {
    "chat_id": chat,
    "text": message,
    "parse_mode": "Markdown",
    "disable_web_page_preview": True,
}

def photo_message():
  if len(bot_offers) > 0:
    data = {
      "chat_id": chat,
      "caption": f"""
🔥 *Nuova offerta*: {bot_offers[0]["Title"]}

🖊️ *Descrizione*: {bot_offers[0]["Description"]}

🔖 *Sconto*: {bot_offers[0]["Discount Percentage"]}%
💰 *Nuovo Prezzo*: {bot_offers[0]["New Price"]} invece di {bot_offers[0]["Old price"]}€

🛒 *Accedi all'offerta*: {bot_offers[0]["Url"]}
""",
    "photo": bot_offers[0]["Img"],
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
      "text": "No more offer to show, next round will be loaded tomorrow",
      #"photo": "https://jooinn.com/images/no-more-1.jpg",
      #"disable_web_page_preview": True,
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

def search_items(page, category):
    access_key = os.getenv("access_key")
    secret_key = os.getenv("secret_key")
    partner_tag = "maulink-21"
    host = "webservices.amazon.it"
    region = "eu-west-1"
    MinSavingPercent = 50
    #keywords = "Harry Potter"
    search_index = category #tutte le opzioni qui https://webservices.amazon.com/paapi5/documentation/locale-reference/italy.html
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
        #print("Complete Response:", response)
        """ Parse response """  
        if response.search_result is not None:
            item_0 = response.search_result.items[0]
            print(f"Lunghezza lista: {len(response.search_result.items)}")
            offers = response.search_result.items
            for offer in offers:
                if offer.offers.listings[0].price.savings is not None:
                  if offer.offers.listings[0].price.savings.percentage > 5:
                    if not {"Title": offer.browse_node_info.browse_nodes[0].display_name, "Description": offer.item_info.title.display_value, "Old price": offer.offers.listings[0].saving_basis.amount, "New Price": offer.offers.listings[0].price.display_amount, "Discount Percentage": offer.offers.listings[0].price.savings.percentage, "Url": offer.detail_page_url, "Img": offer.images.primary.large.url} in bot_offers:
                      bot_offers.append({"Title": offer.browse_node_info.browse_nodes[0].display_name, "Description": offer.item_info.title.display_value, "Old price": offer.offers.listings[0].saving_basis.amount, "New Price": offer.offers.listings[0].price.display_amount, "Discount Percentage": offer.offers.listings[0].price.savings.percentage, "Url": offer.detail_page_url, "Img": offer.images.primary.large.url})
                      print("--------------")
                      print(offer.browse_node_info.browse_nodes[0].display_name, offer.offers.listings[0].price.savings.percentage)
                      print("--------------")
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
  global tasks
  tasks = tasks + 1
  if len(chosen_categories) == 1:
    for page in range(1,6):
        search_items(page, chosen_categories[0])
        time.sleep(2)
  else:
    for category in chosen_categories:
        for page in range(1,6):
          search_items(page, category)
          time.sleep(3)


schedule.every().day.at("08:00:00").do(empty_offers)
schedule.every().day.at("08:00:30").do(main)
for post_time in scheduled_time:
   schedule.every().day.at(post_time).do(photo_message)

while True:
    if len(bot_offers) > 0:
      schedule.run_pending()
    else:
      schedule.run_pending()
      time.sleep(3)
      print(f"Tasks: {tasks}")
      if tasks > 0:
       schedule.run_pending()
       tasks -= 1




#DA MODIFICARE
# I doppioni non li elimina perché hanno ASIN o Img diverso? Dovrei confrontere i Title per eliminarli 
#Fare in modo che se si parla in privato con il bot possa dire se vuole un suo canale amazon
#scheduled time, lo prende così come le api da un file txt

#4. Gamification
#Sistema di punti: Premia gli utenti attivi (ad esempio, che cliccano sui link o condividono offerte) con punti da convertire in vantaggi, come accesso a offerte esclusive.
#Classifiche: Mostra una classifica degli utenti più attivi o di quelli che hanno trovato le migliori offerte.
#Quiz e premi: Organizza quiz o piccoli giochi con premi legati a offerte.
#Vinci buono Amazon
#Deve avvisare il proprietario che non ci sono altre offerte disponibilie

#FUTURO
# prendere anche le recensioni e chi lo spedisce


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
