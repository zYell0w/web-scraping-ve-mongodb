#Yapılan web scrapingler ekranda gösterilmeyip databaseye kaydedilmektedir.
#Web scraping için dergipark.org.tr adresi kullanılmaktadır.
#Arama butonuna makalesi istenen kelimeler girildikten sonra pdfleri pdf klosörüne inecek, makaleler de database üzerinden gözükecektir.
#hızlı bir test için, tekli aratma linkini kullanılması önerilir.

from tkinter import *
from pymongo import MongoClient
import requests
from bs4 import BeautifulSoup
import string

#mongo db bağlantısı
client = MongoClient("localhost",27017)
client = MongoClient("mongodb://localhost:27017/?directConnection=true") 

db = client.neuraldb
articledb = db.articledb

def arat():
    #aratılacak metnin girişi
    metin = arama_entry.get()
    arama_metin = metin.replace(" ","+")
    label.config(text="Aramaniz tamamlanmistir, lütfen kontrol ediniz.",font=("Arial",25))

    base_url = "https://dergipark.org.tr/tr/"
   
    url = base_url + f"search?q={arama_metin}&section=articles"

    response = requests.get(url,verify=False)
    soup = BeautifulSoup(response.text, "lxml")

    articles = soup.find_all("div",{"class":"card-body"})

    article_links = [article.find("a")["href"] for article in articles]

    #tekli aratma için örnek link
    link = ["https://dergipark.org.tr/tr/pub/antropolojidergisi/issue/60325/876686"]

    #tekli arama için "article_links" değişkenini "link" ile değiştirin.
    for i in article_links:
        url = i
        articledb.update_one({"URL":f"{i}"},{"$set":{"URL": f"{i}"}},upsert=True)
        response = requests.get(url,verify=False)
        soup = BeautifulSoup(response.text, "lxml")

        try:
            ozet = soup.find_all("div",{"class":"article-abstract data-section"})
            oz = [metin.find("p").text.strip() for metin in ozet]
            if oz[0] == "-":
                oz.pop(0)
            ozet1 = oz[0]
            
        except Exception as e:
            print(f"hata oldu: {e}")
            ozet1 = "Bulunmamaktadir"

        articledb.update_one({"URL":f"{i}"},{"$set":{"Ozet":f"{ozet1}"}})

        title = soup.find("h3",{"class":"article-title"}).text.strip()
        articledb.update_one({"URL":f"{i}"},{"$set":{"Yayin Adi":f"{title}"}})

        author = soup.find("p",{"class":"article-authors"}).text
        author = author.split()
        author = ' '.join(map(str, author))
        articledb.update_one({"URL":f"{i}"},{"$set":{"Yazar":f"{author}"}})
        

        try:
            doi = soup.find("a",{"class":"doi-link"})["href"]
        except Exception as e:
            print(f"hata oldu: {e}")
            doi = "Bulunmamaktadir."
        
        articledb.update_one({"URL":f"{i}"},{"$set":{"Doi":f"{doi}"}})
        
        try:
            article_k = soup.find_all("div",{"class":"article-keywords data-section"})
            article_keys = [metin.find("p").text.strip() for metin in article_k]
            if article_keys[0] == "-":
                article_keys.pop(0)
        except Exception as e:
            print(f"hata oldu: {e}")
            article_keys ="Bulunmamaktadir."

        articledb.update_one({"URL":f"{i}"},{"$set":{"Anahtar Kelimeler":article_keys}})

        table = soup.find("table",{"class":"record_properties table"})   
        rows = [satir.find("tr") for satir in table]
        for j in rows:
            data = soup.find_all("td")
            data_th = soup.find_all("th")
            row = [tr.text.strip() for tr in data]
            row_th = [tr.text.strip() for tr in data_th]
     
        try:
            publish_type = row[row_th.index("Bölüm")]
        except Exception as e:
            print(f"hata oldu: {e}")
            publish_type ="Bulunmamaktadir."
        articledb.update_one({"URL":f"{i}"},{"$set":{"Yayin Turu":f"Makale"}})

        try:
            publish_time = row[row_th.index("Yayımlanma Tarihi")]
        except Exception as e:
            print(f"hata oldu: {e}")
            publish_time = "Bulunmamaktadir."
        articledb.update_one({"URL":f"{i}"},{"$set":{"Yayin Zamani":f"{publish_time}"}})
        
        try:
            pdf = soup.find("a",{"class":"btn btn-sm float-left article-tool pdf d-flex align-items-center"})["href"]
            pdf = base_url[:-4]+ pdf
        except Exception as e:
            print(f"hata oldu: {e}")
            pdf = "Bulunmamaktadir."
        articledb.update_one({"URL":f"{i}"},{"$set":{"PDF Link":f"{pdf}"}})

        try:
            publisher = soup.find("h1",{"id":"journal-title"}).text
        except Exception as e:
            print(f"hata oldu: {e}")
            publisher = "Dergi Park."
        articledb.update_one({"URL":f"{i}"},{"$set":{"Yayinci Adi":publisher}})
        
        aratilan_kelimeler = metin.split()
        articledb.update_one({"URL":f"{i}"},{"$set":{"Aratilan Kelimeler":aratilan_kelimeler}})

        #SONUCU ÇIKAN HER MAKALE ICIN PDF INDIRME KISMI
        response = requests.get(pdf)
        with open(f'./PDF/{title}.pdf', 'wb') as f:
            f.write(response.content)

    #data basenin tamamını yazdırmak için
    #metin2 = articledb.find({})
    #for list in metin2:
        #for k,v in list.items():
            #gecici = Frame(makaleler,bg="black",relief="raised").pack()
            #Label(gecici,text=f"{k} : {v}").pack()


    


window = Tk()
window.geometry("800x600")
window.title("Makale Motoru")
arama = Frame(window)
makaleler = Frame(window)
arama_entry = Entry(arama)
arama_entry.config(width="200")
arama_entry.pack()
buton = Button(arama,command=arat,text="Yazdir")
buton.pack()
label = Label(arama)
label.pack()  
arama.pack(side=TOP)
makaleler.config(relief="raised")
makaleler.pack(side=BOTTOM)
window.mainloop()